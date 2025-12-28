import asyncio
import json
import os
import queue
import signal
import threading
from concurrent import futures
from typing import List

import grpc
import websockets
from pydantic import BaseModel, ValidationError

from ms_stt import logs
from ms_stt.protos import stt_pb2_grpc
from ms_stt.protos.stt_pb2 import FinalTranscript, STTResponse

log = logs.get_logger()

VOSK_URI = os.getenv("VOSK_URI", "ws://localhost:2700")

# =========================
# Vosk parsing models
# =========================


class VoskEmptyResult(BaseModel):
    pass


class VoskToken(BaseModel):
    conf: float
    end: float
    start: float
    word: str


class VoskResult(BaseModel):
    result: List[VoskToken] | None = None
    text: str


def parse_vosk(data: dict):
    try:
        if "result" in data:
            return VoskResult(**data)
    except ValidationError:
        log.error("Failed to parse Vosk data", extra={"data": data}, exc_info=True)
    return VoskEmptyResult()


# =========================
# gRPC STT Service
# =========================


class STTService(stt_pb2_grpc.SpeechToTextServicer):
    def __init__(self, vosk_uri: str):
        self.vosk_uri = vosk_uri

    def StreamTranscribe(self, request_iterator, context):
        """
        Bidirectional streaming: yields STTResponse whenever Vosk returns a final result
        """
        log.info("Starting stream transcription")
        return self._handle_stream_sync(request_iterator, context)

    def _handle_stream_sync(self, request_iterator, context):
        audio_queue = queue.Queue()
        stop_event = threading.Event()  # <-- define it here

        # -------------------------
        # Feed audio from client
        # -------------------------
        def feed_audio():
            try:
                for req in request_iterator:
                    if req.HasField("audio"):
                        audio_queue.put(req.audio.audio)
                    elif req.HasField("end"):
                        log.info("Client sent EndOfStream")
                        break
            except grpc.RpcError as e:
                # Safe logging: check for 'code' attribute
                code = getattr(e, "code", None)
                if callable(code):
                    log.info(f"Feed audio stopped due to RPC cancellation: {code()}")
                else:
                    log.info(f"Feed audio stopped due to RPC cancellation: {e}")
            finally:
                stop_event.set()

        threading.Thread(target=feed_audio, daemon=True).start()

        # -------------------------
        # Async websocket loop
        # -------------------------
        async def websocket_loop():
            async with websockets.connect(self.vosk_uri) as ws:
                # Send dummy config to Vosk
                await ws.send(json.dumps({"config": {"sample_rate": 16000}}))

                while not stop_event.is_set():
                    # 1. Send audio if available
                    try:
                        audio_chunk = audio_queue.get(timeout=0.1)
                        await ws.send(audio_chunk)
                    except queue.Empty:
                        # No audio to send right now
                        pass

                    # 2. Receive Vosk messages
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=0.05)
                        parsed = parse_vosk(json.loads(msg))
                        if isinstance(parsed, VoskResult) and parsed.text.strip():
                            # Yield immediately as soon as Vosk returns final result
                            yield STTResponse(
                                final=FinalTranscript(text=parsed.text, confidence=0.0)
                            )
                    except asyncio.TimeoutError:
                        continue
                    except websockets.ConnectionClosed:
                        log.info("Vosk websocket closed")
                        break

        # -------------------------
        # Bridge async generator to gRPC generator
        # -------------------------
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async_gen = websocket_loop()
        try:
            while True:
                try:
                    # Get next result from async generator
                    response = loop.run_until_complete(async_gen.__anext__())
                    yield response
                except StopAsyncIteration:
                    # Generator is exhausted, exit loop
                    break
                except asyncio.CancelledError:
                    # Server is shutting down, exit gracefully
                    log.info("Websocket async generator cancelled")
                    break
        except grpc.RpcError as e:
            # Optional: handle if client cancels the RPC
            log.info(f"gRPC RPC cancelled: {e.code()}")


# =========================
# Serve gRPC
# =========================


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    stt_service = STTService(vosk_uri=VOSK_URI)
    stt_pb2_grpc.add_SpeechToTextServicer_to_server(stt_service, server)

    server.add_insecure_port("[::]:50051")
    server.start()
    log.info("🟢 STT gRPC server running on port 50051")

    try:
        # Keep main thread alive
        while True:
            signal.pause()
    except KeyboardInterrupt:
        log.info("🛑 Stopping gRPC server...")
        server.stop(grace=5)  # wait up to 5 seconds for ongoing RPCs to finish
        log.info("Server stopped")


if __name__ == "__main__":
    serve()

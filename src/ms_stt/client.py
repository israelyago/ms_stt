import queue
import threading
import uuid

import grpc
import numpy as np
import sounddevice as sd

from ms_stt import logs
from ms_stt.protos import stt_pb2, stt_pb2_grpc

log = logs.get_logger()

# -----------------------------
# Audio and gRPC settings
# -----------------------------
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 1024  # frames per chunk

audio_queue = queue.Queue()
stop_event = threading.Event()


# -----------------------------
# Audio callback
# -----------------------------
def audio_callback(indata, frames, time, status):
    if status:
        log.info(f"Audio callback status: {status}")
    # Convert float32 -> int16 PCM
    pcm16 = (indata * 32767).astype(np.int16)
    audio_bytes = pcm16.tobytes()
    audio_queue.put(audio_bytes)
    # log.debug(
    #     f"Audio chunk queued: {len(audio_bytes)} bytes, "
    #     f"min={pcm16.min()}, max={pcm16.max()}, mean={pcm16.mean():.2f}"
    # )


# -----------------------------
# Audio generator for gRPC
# -----------------------------
def request_generator():
    log.info("Request generator started")
    # 1. Send STTConfig first
    yield stt_pb2.STTRequest(
        config=stt_pb2.STTConfig(
            session_id=str(uuid.uuid4()),
            sample_rate_hz=SAMPLE_RATE,
            channels=CHANNELS,
            encoding="LINEAR16",
        )
    )

    log.info("STTConfig sent")

    # 2. Stream audio continuously
    while not stop_event.is_set() or not audio_queue.empty():
        try:
            chunk = audio_queue.get(timeout=0.1)
            # log.debug(
            #     f"Sending chunk size={len(chunk)} bytes, first 10 samples={list(chunk[:20])}"
            # )
            yield stt_pb2.STTRequest(audio=stt_pb2.AudioChunk(audio=chunk))
        except queue.Empty:
            log.debug("Audio queue empty")
            continue

    log.info("Sending EndOfStream")
    # 3. Optionally signal end of stream
    yield stt_pb2.STTRequest(end=stt_pb2.EndOfStream())


# -----------------------------
# Main client function
# -----------------------------
def main():
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = stt_pb2_grpc.SpeechToTextStub(channel)

        # Start microphone
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            blocksize=CHUNK_SIZE,
            callback=audio_callback,
        ):
            log.info("🎤 Streaming audio... Speak now!")

            # Call bidirectional streaming
            try:
                responses = stub.StreamTranscribe(request_generator())

                # Receive final transcripts as they come
                for response in responses:
                    if response.HasField("final"):
                        log.info(f"📝 Final transcription: {response.final.text}")
                        log.info(f"Confidence: {response.final.confidence:.2f}")
                    elif response.HasField("error"):
                        log.error(f"❌ STT Error: {response.error.message}")
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.UNAVAILABLE:
                    log.info("Server stopped: streaming RPC cancelled")
                else:
                    log.exception("gRPC streaming RPC failed", exc_info=e)
            finally:
                stop_event.set()


# -----------------------------
if __name__ == "__main__":
    main()

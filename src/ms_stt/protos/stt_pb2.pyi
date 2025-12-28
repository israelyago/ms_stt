from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class STTRequest(_message.Message):
    __slots__ = ("config", "audio", "end")
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    AUDIO_FIELD_NUMBER: _ClassVar[int]
    END_FIELD_NUMBER: _ClassVar[int]
    config: STTConfig
    audio: AudioChunk
    end: EndOfStream
    def __init__(self, config: _Optional[_Union[STTConfig, _Mapping]] = ..., audio: _Optional[_Union[AudioChunk, _Mapping]] = ..., end: _Optional[_Union[EndOfStream, _Mapping]] = ...) -> None: ...

class STTConfig(_message.Message):
    __slots__ = ("session_id", "sample_rate_hz", "channels", "encoding")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_RATE_HZ_FIELD_NUMBER: _ClassVar[int]
    CHANNELS_FIELD_NUMBER: _ClassVar[int]
    ENCODING_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    sample_rate_hz: int
    channels: int
    encoding: str
    def __init__(self, session_id: _Optional[str] = ..., sample_rate_hz: _Optional[int] = ..., channels: _Optional[int] = ..., encoding: _Optional[str] = ...) -> None: ...

class AudioChunk(_message.Message):
    __slots__ = ("audio",)
    AUDIO_FIELD_NUMBER: _ClassVar[int]
    audio: bytes
    def __init__(self, audio: _Optional[bytes] = ...) -> None: ...

class EndOfStream(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class STTResponse(_message.Message):
    __slots__ = ("final", "error")
    FINAL_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    final: FinalTranscript
    error: STTError
    def __init__(self, final: _Optional[_Union[FinalTranscript, _Mapping]] = ..., error: _Optional[_Union[STTError, _Mapping]] = ...) -> None: ...

class FinalTranscript(_message.Message):
    __slots__ = ("text", "confidence")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    text: str
    confidence: float
    def __init__(self, text: _Optional[str] = ..., confidence: _Optional[float] = ...) -> None: ...

class STTError(_message.Message):
    __slots__ = ("message", "code")
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    CODE_FIELD_NUMBER: _ClassVar[int]
    message: str
    code: int
    def __init__(self, message: _Optional[str] = ..., code: _Optional[int] = ...) -> None: ...

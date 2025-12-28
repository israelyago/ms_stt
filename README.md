# Speech to Text
## Setup
Download your vosk model from [here](https://alphacephei.com/vosk/models), make sure to extract the model folder to `vosk_models`

## Running locally
Create a network with:
```sh
podman network create clara-net
```

Run the Vosk server with (Adapt to your model):
```sh
podman run \
  --name vosk \
  --network clara-net \
  -p 2700:2700 \
  -v $(pwd)/vosk_models/vosk-model-en-us-0.42-gigaspeech:/opt/vosk-model-en/model \
  docker.io/alphacep/kaldi-en:latest
```
### With uv
```sh
uv run python src/main.py
```
### With podman
```sh
podman run \
  -it \
  --name ms-stt \
  --network clara-net \
  -p 50051:50051 \
  -e VOSK_URI="ws://vosk:2700" \
  --rm \
  ms-stt
```


## Development
After changing protos schema, run:
```sh
uv run python -m grpc_tools.protoc \
  -I=src \
  --python_out=src \
  --pyi_out=src \
  --grpc_python_out=src \
  src/ms_stt/protos/stt.proto
```
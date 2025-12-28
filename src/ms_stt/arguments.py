import argparse
import sounddevice as sd

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

_parser = argparse.ArgumentParser(description="ASR Server",
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
_parser.add_argument(
    "-r", "--release", help="Run as a release version", action="store_true"
)
_parser.add_argument('-l', '--list-devices', action='store_true',
                    help='show list of audio devices and exit')
_parser.add_argument('-s', '--samplerate', type=int, help='sampling rate', default=16000)
_parser.add_argument('-u', '--uri', type=str, metavar='URL',
                    help='Server URL', default='ws://localhost:2700')
_parser.add_argument('-d', '--device', type=int_or_str,
                    help='input device (numeric ID or substring)')
_parser.add_argument(
    "--logs", help="Folder path to save the logs", default="logs"
)

_args = _parser.parse_args()
if _args.list_devices:
    print(sd.query_devices())
    _parser.exit(0)

def get_args():
    return _args
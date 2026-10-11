"""Back-compat wrapper. The archive standard now lives in speech_align.py.

snap(folder, published_seconds) -> (seconds, why)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from speech_align import play_start


def snap(folder, published, lookback=30):
    s, kind, why = play_start(folder, published, lookback)
    return s, why


if __name__ == "__main__":
    print(*snap(sys.argv[1], float(sys.argv[2])))

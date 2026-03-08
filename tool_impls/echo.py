import json
import sys


def main() -> int:
    raw = sys.stdin.read()
    payload = json.loads(raw)

    text = payload.get("text", "")
    result = {"echoed": text}

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

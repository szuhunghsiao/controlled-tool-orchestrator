import json
import sys


def main() -> int:
    raw = sys.stdin.read()
    payload = json.loads(raw)

    a = payload["a"]
    b = payload["b"]

    print(json.dumps({"sum": a + b}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

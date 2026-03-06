import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    # production 方向：統一輸出到 stdout，讓部署環境收集（即使你不使用 Docker 也同理）
    handler = logging.StreamHandler(sys.stdout)
    fmt = "%(levelname)s %(name)s %(message)s"
    handler.setFormatter(logging.Formatter(fmt))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

import datetime as dt
from dataclasses import dataclass

@dataclass
class AppConfig:
    time: dt.datetime
    until: dt.datetime
    prio_max: int = 7
    metric: str = "cpu"
    log_limit: int = 2000


def parse_timestamp(s: str) -> dt.datetime:
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]:
        try:
            return dt.datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise SystemExit(f"Invalid time format: {s}")

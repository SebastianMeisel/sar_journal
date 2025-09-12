from dataclasses import dataclass
import datetime as dt


@dataclass
class AppConfig:
    """
    Configuration for the application runtime.

    Attributes:
        time (dt.datetime): The starting time for data processing.
        until (dt.datetime): The ending time until which data is considered.
        prio_max (int): Maximum priority level to include in processing
                        (default: 7).
        metric (str): Name of the metric to analyze (default: "cpu").
        log_limit (int): Maximum number of log entries to process
                         (default: 2000).
    """

    time: dt.datetime
    until: dt.datetime
    prio_max: int = 7
    metric: str = "cpu"
    log_limit: int = 2000


def parse_timestamp(s: str) -> dt.datetime:
    """
    Parse a timestamp string into a datetime object.

    The function accepts two formats:
    - "%Y-%m-%d %H:%M:%S"
    - "%Y-%m-%d %H:%M"

    Args:
        s (str): The timestamp string to parse.

    Returns:
        dt.datetime: The parsed datetime object.

    Raises:
        SystemExit: If the input string does not match any known format.
    """
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]:
        try:
            return dt.datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise SystemExit(f"Invalid time format: {s}")

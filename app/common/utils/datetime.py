from datetime import datetime, timezone


def datetime_utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)

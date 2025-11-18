import datetime as dt

UTC = dt.timezone.utc


def utc_now() -> dt.datetime:
    """Return the current UTC time as an aware datetime."""
    return dt.datetime.now(UTC)


def ensure_utc(value: dt.datetime | None) -> dt.datetime | None:
    """Normalize datetimes to UTC timezone-aware instances."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def parse_iso_datetime(value: str | None) -> dt.datetime | None:
    """Parse an ISO 8601 string into a UTC-aware datetime."""
    if not value:
        return None
    iso_value = value.strip()
    if iso_value.endswith("Z"):
        iso_value = iso_value[:-1] + "+00:00"
    parsed = dt.datetime.fromisoformat(iso_value)
    return ensure_utc(parsed)

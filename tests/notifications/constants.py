import re
from typing import Final

ALLOWED_DEEP_LINK_PAYLOAD_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"[A-Za-z0-9\-_]{0,64}"
)
TELEGRAM_CONNECTION_LINK_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"https://t\.me/(?P<bot_username>\w+?)"
    rf"\?start=(?P<link_payload>{ALLOWED_DEEP_LINK_PAYLOAD_PATTERN.pattern})"
)

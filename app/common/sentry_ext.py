from sentry_sdk.types import Breadcrumb, BreadcrumbHint


def before_breadcrumb(crumb: Breadcrumb, _hint: BreadcrumbHint) -> Breadcrumb | None:
    if crumb.get("category") == "redis":
        redis_command = crumb.get("data", {}).get("redis.command")
        if redis_command in {"PING", "XREADGROUP", "XGROUP CREATE"}:
            return None
    return crumb

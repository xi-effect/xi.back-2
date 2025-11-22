from sentry_sdk.types import Breadcrumb, BreadcrumbHint


def before_breadcrumb(crumb: Breadcrumb, _hint: BreadcrumbHint) -> Breadcrumb | None:
    crumb_category = crumb.get("category")
    crumb_data = crumb.get("data", {})
    if crumb_category == "redis":
        redis_command = crumb_data.get("redis.command")
        if redis_command in {"PING", "XREADGROUP", "XGROUP CREATE", "XACK"}:
            return None
    elif crumb_category == "httplib":
        http_url: str = crumb_data.get("url")
        if http_url.endswith(("setWebhook", "setMyCommands", "getMe")):
            return None
    return crumb

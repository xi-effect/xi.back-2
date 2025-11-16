from faststream.redis import StreamSub

from app.common.config import settings


def build_stream_sub(stream_name: str, service_name: str) -> StreamSub:
    return StreamSub(
        stream=stream_name,
        group=service_name,
        consumer=settings.instance_name,
    )

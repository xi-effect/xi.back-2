from typing import Any

from fastapi import Depends
from pydantic import TypeAdapter
from tmexio import TMEXIO, AsyncSocket, Emitter
from tmexio.specs import EmitterSpec


class TMEXIOExt(TMEXIO):
    def register_server_emitter_fastapi_depends(
        self,
        body_annotation: Any,
        event_name: str,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> Any:
        # TODO support this in tmexio & switch to a system with routers
        type_adapter = TypeAdapter(body_annotation)

        self.add_emitter(
            event_name=event_name,
            spec=EmitterSpec(
                summary=summary,
                description=description,
                tags=tags or [],
                body_model=type_adapter,
            ),
        )

        def build_emitter() -> Emitter[Any]:
            return Emitter(
                socket=AsyncSocket(server=self.server, sid=""),
                event_name=event_name,
                adapter=type_adapter,
            )

        return Depends(build_emitter)

from typing import Any

from pydantic import TypeAdapter

from app.common.bridges.base_bdg import BaseBridge
from app.common.bridges.utils import ResponsePipelineBuilder
from app.common.config import settings
from app.common.schemas.autocomplete_sch import TagKind, TagSchema

tag_id_to_tag_dict_type_adapter = TypeAdapter(dict[int, TagSchema])


class AutocompleteBridge(BaseBridge):
    def __init__(self) -> None:
        super().__init__(
            base_url=f"{settings.bridge_base_url}/internal/autocomplete-service",
            headers={"X-Api-Key": settings.api_key},
        )

    async def retrieve_multiple_tags(
        self,
        kind: TagKind,
        tag_ids: list[int],
        tutor_id: int | None = None,
    ) -> dict[int, TagSchema]:
        params: dict[str, Any] = {"tag_ids": tag_ids}
        if tutor_id is not None:
            params["tutor_id"] = tutor_id
        return (
            await ResponsePipelineBuilder.initialize_from_request(
                self.client.get(
                    f"/tag-kinds/{kind}/tags/",
                    params=params,
                )
            )
            .validate_status_code()
            .validate_json(tag_id_to_tag_dict_type_adapter)
        )

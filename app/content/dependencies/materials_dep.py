from starlette import status

from app.common.fastapi_ext import Responses


class MaterialResponses(Responses):
    MATERIAL_NOT_FOUND = status.HTTP_404_NOT_FOUND, "Material not found"


class MyMaterialResponses(Responses):
    MATERIAL_ACCESS_DENIED = status.HTTP_403_FORBIDDEN, "Material access denied"

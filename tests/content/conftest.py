import wave
from collections.abc import AsyncIterator
from dataclasses import dataclass
from io import BytesIO
from os import stat
from pathlib import Path as PathlibPath
from typing import Any, Protocol
from uuid import UUID, uuid4

import pytest
from faker import Faker
from faker_file.providers.pdf_file.generators.pil_generator import (  # type: ignore[import-untyped]
    PilPdfGenerator,
)
from PIL import Image
from pytest_lazy_fixtures import lf
from starlette.responses import FileResponse
from starlette.testclient import TestClient

from app.common.config import content_token_provider, settings
from app.common.dependencies.authorization_dep import ProxyAuthData
from app.common.filetype_ext import PRESENTATION_CONTENT_TYPE
from app.content.models.files_db import ContentDisposition, File, FileKind
from app.content.models.materials_db import (
    ClassroomMaterial,
    ClassroomNoteMaterial,
    Material,
    PersonalMaterial,
)
from app.content.models.ydoc_files_db import YDocFile
from app.content.models.ydocs_db import YDoc, YDocContentKind
from tests.common.active_session import ActiveSession
from tests.common.types import AnyJSON, PytestRequest
from tests.content import factories
from tests.factories import ProxyAuthDataFactory


class ContentTokenGeneratorProtocol(Protocol):
    def __call__(
        self,
        material_id: UUID,
        ydoc_id: UUID,
        user_id: int,
        **overrides: Any,
    ) -> str:
        pass


@pytest.fixture(scope="session")
def content_token_generator() -> ContentTokenGeneratorProtocol:
    def content_token_generator_inner(
        material_id: UUID,
        ydoc_id: UUID,
        user_id: int,
        **overrides: Any,
    ) -> str:
        return content_token_provider.serialize_and_sign(
            factories.ContentTokenPayloadFactory.build(
                material_id=material_id,
                ydoc_id=ydoc_id,
                user_id=user_id,
                **overrides,
            )
        )

    return content_token_generator_inner


@pytest.fixture()
def material_id() -> UUID:
    return uuid4()


@pytest.fixture()
def outsider_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def outsider_user_id(outsider_auth_data: ProxyAuthData) -> int:
    return outsider_auth_data.user_id


@pytest.fixture()
def outsider_internal_client(
    client: TestClient,
    outsider_auth_data: ProxyAuthData,
) -> TestClient:
    return TestClient(
        client.app,
        headers={
            **outsider_auth_data.as_headers,
            "X-Api-Key": settings.api_key,
        },
    )


@pytest.fixture()
def outsider_client(
    client: TestClient,
    outsider_auth_data: ProxyAuthData,
) -> TestClient:
    return TestClient(client.app, headers=outsider_auth_data.as_headers)


@pytest.fixture()
def tutor_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def tutor_user_id(tutor_auth_data: ProxyAuthData) -> int:
    return tutor_auth_data.user_id


@pytest.fixture()
def tutor_client(client: TestClient, tutor_auth_data: ProxyAuthData) -> TestClient:
    return TestClient(client.app, headers=tutor_auth_data.as_headers)


@pytest.fixture()
def student_auth_data() -> ProxyAuthData:
    return ProxyAuthDataFactory.build()


@pytest.fixture()
def student_user_id(student_auth_data: ProxyAuthData) -> int:
    return student_auth_data.user_id


@pytest.fixture()
def student_client(client: TestClient, student_auth_data: ProxyAuthData) -> TestClient:
    return TestClient(client.app, headers=student_auth_data.as_headers)


@pytest.fixture()
def ydoc_owner_id(faker: Faker) -> int:
    return faker.pyint(min_value=1, max_value=1000000)


@pytest.fixture()
async def ydoc(
    faker: Faker,
    active_session: ActiveSession,
    ydoc_owner_id: int,
) -> AsyncIterator[YDoc]:
    content: bytes = faker.binary(length=64)

    async with active_session():
        ydoc = await YDoc.create(
            owner_id=ydoc_owner_id,
            content_kind=YDocContentKind.NOTE,
            content=content,
            size_bytes=len(content),
        )

    yield ydoc

    async with active_session():
        await YDoc.delete_by_kwargs(id=ydoc.id)


@pytest.fixture()
async def other_ydoc(
    faker: Faker,
    active_session: ActiveSession,
) -> AsyncIterator[YDoc]:
    content: bytes = faker.binary(length=64)

    async with active_session():
        ydoc = await YDoc.create(
            owner_id=faker.pyint(min_value=1, max_value=1000000),
            content_kind=YDocContentKind.NOTE,
            content=content,
            size_bytes=len(content),
        )

    yield ydoc

    async with active_session():
        await YDoc.delete_by_kwargs(id=ydoc.id)


@pytest.fixture()
def missing_ydoc_id() -> UUID:
    return uuid4()


@pytest.fixture()
def uncategorized_file_content(faker: Faker) -> bytes:
    return faker.bin_file(raw=True)  # type: ignore[no-any-return]


def process_image_content(image_content: bytes) -> bytes:
    image = Image.open(BytesIO(image_content))
    processed_image_buffer = BytesIO()
    image.save(processed_image_buffer, format="webp")
    processed_image_buffer.seek(0)
    return processed_image_buffer.read()


@pytest.fixture()
def webp_image_file_content(faker: Faker) -> bytes:
    return faker.graphic_webp_file(raw=True)  # type: ignore[no-any-return]


@pytest.fixture()
def png_image_file_content(faker: Faker) -> bytes:
    return faker.graphic_png_file(raw=True)  # type: ignore[no-any-return]


@dataclass
class FileInputData:
    kind: FileKind
    name: str
    content_type: str
    input_content: bytes
    processed_content: bytes

    @property
    def stem(self) -> str:
        return PathlibPath(self.name).stem

    @property
    def extension(self) -> str:
        return PathlibPath(self.name).suffix.lstrip(".")

    @property
    def stored_content_type(self) -> str:
        return "image/webp" if self.kind == FileKind.IMAGE else self.content_type

    @property
    def content_disposition(self) -> ContentDisposition:
        attachment_kinds = {FileKind.UNCATEGORIZED, FileKind.PRESENTATION}
        return "attachment" if self.kind in attachment_kinds else "inline"


@pytest.fixture()
def uncategorized_file_input_data(
    faker: Faker,
    uncategorized_file_content: bytes,
) -> FileInputData:
    return FileInputData(
        kind=FileKind.UNCATEGORIZED,
        name=faker.file_name(),
        input_content=uncategorized_file_content,
        processed_content=uncategorized_file_content,
        content_type=faker.mime_type(category="application"),
    )


@pytest.fixture()
def webp_image_file_input_data(
    faker: Faker,
    webp_image_file_content: bytes,
) -> FileInputData:
    return FileInputData(
        kind=FileKind.IMAGE,
        name=faker.file_name(extension="webp"),
        input_content=webp_image_file_content,
        processed_content=process_image_content(webp_image_file_content),
        content_type="image/webp",
    )


@pytest.fixture()
def png_image_file_input_data(
    faker: Faker,
    png_image_file_content: bytes,
) -> FileInputData:
    return FileInputData(
        kind=FileKind.IMAGE,
        name=faker.file_name(extension="png"),
        input_content=png_image_file_content,
        processed_content=process_image_content(png_image_file_content),
        content_type="image/png",
    )


@pytest.fixture()
def pdf_document_file_content(faker: Faker) -> bytes:
    return faker.pdf_file(  # type: ignore[no-any-return]
        pdf_generator_cls=PilPdfGenerator,
        raw=True,
    )


@pytest.fixture()
def pdf_document_file_input_data(
    faker: Faker,
    pdf_document_file_content: bytes,
) -> FileInputData:
    return FileInputData(
        kind=FileKind.DOCUMENT,
        name=faker.file_name(extension="pdf"),
        input_content=pdf_document_file_content,
        processed_content=pdf_document_file_content,
        content_type="application/pdf",
    )


@pytest.fixture()
def wav_audio_file_content(faker: Faker) -> bytes:
    audio_content = BytesIO()
    with wave.open(audio_content, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(44100)
        f.writeframes(faker.binary(44100))
    return audio_content.getvalue()


@pytest.fixture()
def wav_audio_file_input_data(
    faker: Faker,
    wav_audio_file_content: bytes,
) -> FileInputData:
    return FileInputData(
        kind=FileKind.AUDIO,
        name=faker.file_name(extension="wav"),
        input_content=wav_audio_file_content,
        processed_content=wav_audio_file_content,
        content_type="audio/x-wav",
    )


@pytest.fixture()
def pptx_presentation_file_content(faker: Faker) -> bytes:
    return faker.pptx_file(raw=True)  # type: ignore[no-any-return]


@pytest.fixture()
def pptx_presentation_file_input_data(
    faker: Faker,
    pptx_presentation_file_content: bytes,
) -> FileInputData:
    return FileInputData(
        kind=FileKind.PRESENTATION,
        name=faker.file_name(extension="pptx"),
        input_content=pptx_presentation_file_content,
        processed_content=pptx_presentation_file_content,
        content_type=PRESENTATION_CONTENT_TYPE,
    )


@pytest.fixture(
    params=[
        pytest.param(lf("uncategorized_file_input_data"), id="uncategorized"),
        pytest.param(lf("webp_image_file_input_data"), id="webp_image"),
        pytest.param(lf("png_image_file_input_data"), id="png_image"),
        pytest.param(lf("pdf_document_file_input_data"), id="pdf_document"),
        pytest.param(lf("wav_audio_file_input_data"), id="wav_audio"),
        pytest.param(lf("pptx_presentation_file_input_data"), id="pptx_presentation"),
    ],
)
def parametrized_file_input_data(
    request: PytestRequest[FileInputData],
) -> FileInputData:
    return request.param


@pytest.fixture()
def file_owner_id(faker: Faker) -> int:
    return faker.pyint(min_value=1, max_value=1000000)


@pytest.fixture()
def file_uploader_id(faker: Faker) -> int:
    return faker.pyint(min_value=1, max_value=1000000)


@pytest.fixture()
async def file(
    active_session: ActiveSession,
    parametrized_file_input_data: FileInputData,
    file_owner_id: int,
    file_uploader_id: int,
) -> AsyncIterator[File]:
    async with active_session():
        file = await File.create(
            owner_id=file_owner_id,
            uploader_id=file_uploader_id,
            name=parametrized_file_input_data.stem,
            extension=parametrized_file_input_data.extension,
            kind=parametrized_file_input_data.kind,
            content_type=parametrized_file_input_data.stored_content_type,
            size_bytes=len(parametrized_file_input_data.processed_content),
        )

    file.path.parent.mkdir(parents=True, exist_ok=True)
    with file.path.open("wb") as f:
        f.write(parametrized_file_input_data.processed_content)

    yield file

    file.path.unlink(missing_ok=True)
    async with active_session():
        await File.delete_by_kwargs(id=file.id)


@pytest.fixture()
def file_data(file: File) -> AnyJSON:
    return File.ResponseSchema.model_validate(file, from_attributes=True).model_dump(
        mode="json"
    )


@pytest.fixture()
async def ydoc_file(
    active_session: ActiveSession,
    ydoc: YDoc,
    file: File,
) -> AsyncIterator[YDocFile]:
    async with active_session():
        ydoc_file = await YDocFile.create(
            ydoc_id=ydoc.id,
            file_id=file.id,
        )

    yield ydoc_file

    async with active_session():
        await YDocFile.delete_by_kwargs(
            ydoc_id=ydoc_file.ydoc_id,
            file_id=ydoc_file.file_id,
        )


@pytest.fixture()
def file_response(file: File) -> FileResponse:
    return FileResponse(file.path, stat_result=stat(file.path))


@pytest.fixture()
def file_etag(file_response: FileResponse) -> str | None:
    return file_response.headers["etag"]


@pytest.fixture()
def file_last_modified(file_response: FileResponse) -> str | None:
    return file_response.headers["last-modified"]


@pytest.fixture()
def missing_file_id() -> UUID:
    return uuid4()


@pytest.fixture()
def classroom_id(faker: Faker) -> int:
    return faker.random_int()


@pytest.fixture()
async def personal_material(
    faker: Faker,
    active_session: ActiveSession,
    tutor_user_id: int,
) -> AsyncIterator[PersonalMaterial]:
    input_data = factories.PersonalMaterialInputFactory.build_python()
    content: bytes = faker.binary(length=64)

    async with active_session():
        main_ydoc = await YDoc.create(
            owner_id=tutor_user_id,
            content_kind=input_data.pop("content_kind"),
            content=content,
            size_bytes=len(content),
        )
        personal_material = await PersonalMaterial.create(
            main_ydoc=main_ydoc,
            tutor_id=tutor_user_id,
            **input_data,
        )

    yield personal_material

    async with active_session():
        await PersonalMaterial.delete_by_kwargs(id=personal_material.id)
        await YDoc.delete_by_kwargs(id=main_ydoc.id)


@pytest.fixture()
async def personal_material_data(personal_material: PersonalMaterial) -> AnyJSON:
    return PersonalMaterial.ResponseSchema.model_validate(
        personal_material, from_attributes=True
    ).model_dump(mode="json")


@pytest.fixture()
async def deleted_personal_material_id(
    active_session: ActiveSession,
    personal_material: PersonalMaterial,
) -> UUID:
    async with active_session():
        await PersonalMaterial.delete_by_kwargs(id=personal_material.id)
    return personal_material.id


@pytest.fixture()
async def classroom_material(
    faker: Faker,
    active_session: ActiveSession,
    tutor_user_id: int,
    classroom_id: int,
) -> AsyncIterator[ClassroomMaterial]:
    input_data = factories.ClassroomMaterialInputFactory.build_python()
    content: bytes = faker.binary(length=64)

    async with active_session():
        main_ydoc = await YDoc.create(
            owner_id=tutor_user_id,
            content_kind=input_data.pop("content_kind"),
            content=content,
            size_bytes=len(content),
        )
        classroom_material = await ClassroomMaterial.create(
            main_ydoc=main_ydoc,
            classroom_id=classroom_id,
            **input_data,
        )

    yield classroom_material

    async with active_session():
        await ClassroomMaterial.delete_by_kwargs(id=classroom_material.id)
        await YDoc.delete_by_kwargs(id=main_ydoc.id)


@pytest.fixture()
async def classroom_material_data(
    classroom_material: ClassroomMaterial,
) -> AnyJSON:
    return ClassroomMaterial.ResponseSchema.model_validate(
        classroom_material, from_attributes=True
    ).model_dump(mode="json")


@pytest.fixture()
async def deleted_classroom_material_id(
    active_session: ActiveSession,
    classroom_material: ClassroomMaterial,
) -> UUID:
    async with active_session():
        await ClassroomMaterial.delete_by_kwargs(id=classroom_material.id)
    return classroom_material.id


@pytest.fixture()
async def classroom_note_material(
    faker: Faker,
    active_session: ActiveSession,
    tutor_user_id: int,
    classroom_id: int,
) -> AsyncIterator[ClassroomNoteMaterial]:
    content: bytes = faker.binary(length=64)

    async with active_session():
        main_ydoc = await YDoc.create(
            owner_id=tutor_user_id,
            content_kind=YDocContentKind.NOTE,
            content=content,
            size_bytes=len(content),
        )
        classroom_note_material = await ClassroomNoteMaterial.create(
            main_ydoc=main_ydoc,
            classroom_id=classroom_id,
        )

    yield classroom_note_material

    async with active_session():
        await ClassroomNoteMaterial.delete_by_kwargs(id=classroom_note_material.id)
        await YDoc.delete_by_kwargs(id=main_ydoc.id)


@pytest.fixture(
    params=[
        pytest.param(lf("personal_material"), id="personal_material"),
        pytest.param(lf("classroom_material"), id="classroom_material"),
        pytest.param(lf("classroom_note_material"), id="classroom_note_material"),
    ],
)
def any_material(request: PytestRequest[Material]) -> Material:
    return request.param


@pytest.fixture()
async def deleted_any_material_id(
    active_session: ActiveSession,
    any_material: Material,
) -> UUID:
    async with active_session():
        await Material.delete_by_kwargs(id=any_material.id)
    return any_material.id

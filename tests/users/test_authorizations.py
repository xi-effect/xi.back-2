import pytest
from starlette import status
from starlette.testclient import TestClient

from app.common.dependencies.authorization_dep import ProxyAuthData
from app.users.models.users_db import OnboardingStage
from tests.common.assert_contains_ext import assert_response
from tests.factories import ProxyAuthDataFactory

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("method", "path"),
    [
        # onboarding_rst
        *[
            pytest.param(
                "PUT",
                f"/users/current/onboarding-stages/{onboarding_stage.value}/",
                id=f"update_onboarding_stage_{onboarding_stage.value}",
            )
            for onboarding_stage in OnboardingStage
        ],
        # current_users_rst
        pytest.param(
            "GET",
            "/users/current/home/",
            id="get_current_user_home",
        ),
        pytest.param(
            "PATCH",
            "/users/current/",
            id="update_current_user",
        ),
        pytest.param(
            "PUT",
            "/users/current/password/",
            id="update_current_user_password",
        ),
        # email_confirmation_rst
        pytest.param(
            "POST",
            "/users/current/email-confirmation/requests/",
            id="request_email_confirmation_resend",
        ),
        # email_change_rst
        pytest.param(
            "POST",
            "/users/current/email-change/requests/",
            id="request_email_change",
        ),
        # avatars_rst
        pytest.param(
            "PUT",
            "/users/current/avatar/",
            id="update_current_user_avatar",
        ),
        pytest.param(
            "DELETE",
            "/users/current/avatar/",
            id="delete_current_user_avatar",
        ),
        # sessions_rst
        pytest.param("GET", "/sessions/current/", id="get_current_session"),
        pytest.param("DELETE", "/sessions/current/", id="signout"),
        pytest.param("GET", "/sessions/", id="list_sessions"),
        pytest.param("DELETE", "/sessions/", id="disable_all_sessions"),
        pytest.param("DELETE", "/sessions/1/", id="disable_session_by_id"),
    ],
)
async def test_requesting_unauthorized(
    client: TestClient,
    method: str,
    path: str,
) -> None:
    assert_response(
        client.request(method, f"/api/protected/user-service{path}"),
        expected_code=status.HTTP_401_UNAUTHORIZED,
        expected_json={"detail": "Proxy auth required"},
    )


@pytest.mark.parametrize(
    ("method", "path"),
    [
        # onboarding_rst
        *[
            pytest.param(
                "PUT",
                f"/users/current/onboarding-stages/{onboarding_stage.value}/",
                id=f"update_onboarding_stage_{onboarding_stage.value}",
            )
            for onboarding_stage in OnboardingStage
        ],
        # current_users_rst
        pytest.param(
            "GET",
            "/users/current/home/",
            id="get_current_user_home",
        ),
        pytest.param(
            "PATCH",
            "/users/current/",
            id="update_current_user",
        ),
        pytest.param(
            "PUT",
            "/users/current/password/",
            id="update_current_user_password",
        ),
        # email_confirmation_rst
        pytest.param(
            "POST",
            "/users/current/email-confirmation/requests/",
            id="request_email_confirmation_resend",
        ),
        # email_change_rst
        pytest.param(
            "POST",
            "/users/current/email-change/requests/",
            id="request_email_change",
        ),
        # avatars_rst
        pytest.param(
            "PUT",
            "/users/current/avatar/",
            id="update_current_user_avatar",
        ),
        pytest.param(
            "DELETE",
            "/users/current/avatar/",
            id="delete_current_user_avatar",
        ),
    ],
)
async def test_requesting_user_not_found(
    client: TestClient,
    user_proxy_auth_data: ProxyAuthData,
    deleted_user_id: int,
    method: str,
    path: str,
) -> None:
    broken_proxy_auth_data: ProxyAuthData = ProxyAuthDataFactory.build(
        session_id=user_proxy_auth_data.session_id,
        user_id=deleted_user_id,
    )

    assert_response(
        client.request(
            method,
            f"/api/protected/user-service{path}",
            headers=broken_proxy_auth_data.as_headers,
        ),
        expected_code=status.HTTP_401_UNAUTHORIZED,
        expected_json={"detail": "User not found"},
    )

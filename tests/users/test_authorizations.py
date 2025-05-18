import pytest
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
                f"/onboarding/stages/{onboarding_stage.value}/",
                id=f"onboarding-proceed-{onboarding_stage.value}",
            )
            for onboarding_stage in OnboardingStage
        ],
        *[
            pytest.param(
                "DELETE",
                f"/onboarding/stages/{onboarding_stage.value}/",
                id=f"onboarding-return-{onboarding_stage.value}",
            )
            for onboarding_stage in OnboardingStage
        ],
        # users_rst
        pytest.param(
            "GET",
            "/users/by-id/1/profile/",
            id="get-profile-by-id",
        ),
        pytest.param(
            "GET",
            "/users/by-username/1/profile/",
            id="get-profile-by-username",
        ),
        # current_users_rst
        pytest.param(
            "GET",
            "/users/current/home/",
            id="get-current-user-home",
        ),
        pytest.param(
            "PATCH",
            "/users/current/profile/",
            id="update-current-user-profile",
        ),
        pytest.param(
            "POST",
            "/users/current/email-confirmation-requests/",
            id="post-email-confirmation-request",
        ),
        pytest.param(
            "PUT",
            "/users/current/email/",
            id="update-current-user-email",
        ),
        pytest.param(
            "PUT",
            "/users/current/password/",
            id="update-current-user-password",
        ),
        # avatars_rst
        pytest.param(
            "PUT",
            "/users/current/avatar/",
            id="update-current-user-avatar",
        ),
        pytest.param(
            "DELETE",
            "/users/current/avatar/",
            id="delete-current-user-avatar",
        ),
        # sessions_rst
        pytest.param("GET", "/sessions/current/", id="get-current-session"),
        pytest.param("DELETE", "/sessions/current/", id="signout"),
        pytest.param("GET", "/sessions/", id="list-sessions"),
        pytest.param("DELETE", "/sessions/", id="disable-all-sessions"),
        pytest.param("DELETE", "/sessions/1/", id="disable-session-by-id"),
    ],
)
async def test_requesting_unauthorized(
    client: TestClient,
    method: str,
    path: str,
) -> None:
    assert_response(
        client.request(method, f"/api/protected/user-service{path}"),
        expected_code=407,
        expected_json={"detail": "Proxy auth required"},
    )


@pytest.mark.parametrize(
    ("method", "path"),
    [
        # onboarding_rst
        *[
            pytest.param(
                "PUT",
                f"/onboarding/stages/{onboarding_stage.value}/",
                id=f"onboarding-proceed-{onboarding_stage.value}",
            )
            for onboarding_stage in OnboardingStage
        ],
        *[
            pytest.param(
                "DELETE",
                f"/onboarding/stages/{onboarding_stage.value}/",
                id=f"onboarding-return-{onboarding_stage.value}",
            )
            for onboarding_stage in OnboardingStage
        ],
        # current_users_rst
        pytest.param(
            "GET",
            "/users/current/home/",
            id="get-current-user-home",
        ),
        pytest.param(
            "PATCH",
            "/users/current/profile/",
            id="update-current-user-profile",
        ),
        pytest.param(
            "POST",
            "/users/current/email-confirmation-requests/",
            id="post-email-confirmation-request",
        ),
        pytest.param(
            "PUT",
            "/users/current/email/",
            id="update-current-user-email",
        ),
        pytest.param(
            "PUT",
            "/users/current/password/",
            id="update-current-user-password",
        ),
        # avatars_rst
        pytest.param(
            "PUT",
            "/users/current/avatar/",
            id="update-current-user-avatar",
        ),
        pytest.param(
            "DELETE",
            "/users/current/avatar/",
            id="delete-current-user-avatar",
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
        expected_code=401,
        expected_json={"detail": "User not found"},
    )

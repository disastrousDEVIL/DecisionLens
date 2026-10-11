from fastapi.testclient import TestClient

from app.main import app


def test_providers_never_include_credentials() -> None:
    response = TestClient(app).get("/api/v1/providers")

    assert response.status_code == 200
    providers = {provider["slug"]: provider for provider in response.json()}
    assert set(providers) == {"jev", "clef-flash", "openai-decisions"}
    assert "api_key" not in str(providers).lower()


def test_unknown_provider_is_rejected() -> None:
    response = TestClient(app).post(
        "/api/v1/compare",
        json={
            "providers": ["unknown"],
            "decision": {
                "state": "My package arrived damaged.",
                "questions": [
                    {
                        "id": "damaged",
                        "primitive": "binary",
                        "instructions": "Is the package damaged?",
                    }
                ],
            },
        },
    )

    assert response.status_code == 422


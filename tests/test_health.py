from django.test import Client
from django.urls import reverse


def test_health_returns_json_ok(client: Client) -> None:
    response = client.get(reverse("health"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response["Content-Type"].startswith("application/json")


def test_health_rejects_methods_other_than_get(client: Client) -> None:
    response = client.post(reverse("health"))

    assert response.status_code == 405

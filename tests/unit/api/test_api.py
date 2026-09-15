import logging

import pytest
from fastapi import status
from fastapi.testclient import TestClient


def test_root_redirect(test_client: TestClient) -> None:
    response = test_client.get("/", follow_redirects=False)

    assert response.status_code == status.HTTP_308_PERMANENT_REDIRECT
    assert response.headers["location"] == "/docs"


def test_register_success(
    test_client: TestClient,
    valid_payload: dict[str, str],
) -> None:
    response = test_client.post("/v1/auth/register", json=valid_payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.text == "OK"


def test_register_invalid_data(
    test_client: TestClient,
    valid_payload: dict[str, str],
) -> None:
    payload = {**valid_payload, "login": "admin"}
    response = test_client.post("/v1/auth/register", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.text == "Логин запрещен"


def test_register_password_mismatch(
    test_client: TestClient,
    valid_payload: dict[str, str],
) -> None:
    payload = {**valid_payload, "confirmPassword": "Другой1!"}
    response = test_client.post("/v1/auth/register", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.text == "Пароль и подтверждение пароля не совпадают"


def test_register_extra_fields_forbidden(
    test_client: TestClient,
    valid_payload: dict[str, str],
) -> None:
    payload = {**valid_payload, "extra": "field"}
    response = test_client.post("/v1/auth/register", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_api_logging_masks_password(
    test_client: TestClient,
    valid_payload: dict[str, str],
    valid_password: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO):
        test_client.post("/v1/auth/register", json=valid_payload)

    assert any(
        "Request successful" in record.message
        and valid_password not in record.message
        for record in caplog.records
    )

from unittest.mock import patch, MagicMock

import pytest
import requests

import app as app_module


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    original = dict(app_module.orders_db)
    with app_module.app.test_client() as c:
        yield c
    app_module.orders_db.clear()
    app_module.orders_db.update(original)


def fake_response(status=200, payload=None):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = payload if payload is not None else {}
    return resp


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.get_json()["service"] == "Order Service"


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "healthy"}


def test_get_all_orders(client):
    r = client.get("/orders")
    assert r.status_code == 200
    assert len(r.get_json()) == 3


@patch("app.requests.get")
def test_get_order_ok(mock_get, client):
    mock_get.return_value = fake_response(200, {"id": 1, "name": "Ana"})
    r = client.get("/orders/1")
    assert r.status_code == 200
    assert r.get_json()["user"]["name"] == "Ana"


def test_get_order_not_found(client):
    r = client.get("/orders/999")
    assert r.status_code == 404


@patch("app.requests.get")
def test_get_order_user_not_found(mock_get, client):
    mock_get.return_value = fake_response(404)
    r = client.get("/orders/1")
    assert r.status_code == 200
    assert r.get_json()["user"] == {"error": "User not found"}


@patch("app.requests.get", side_effect=requests.exceptions.ConnectionError())
def test_get_order_user_service_down(mock_get, client):
    r = client.get("/orders/1")
    assert r.status_code == 200
    assert r.get_json()["user"] == {"error": "User service unavailable"}


@patch("app.requests.get")
def test_orders_by_user_ok(mock_get, client):
    mock_get.return_value = fake_response(200, {"id": 1})
    r = client.get("/orders/user/1")
    assert r.status_code == 200
    assert len(r.get_json()) == 2


@patch("app.requests.get")
def test_orders_by_user_not_found(mock_get, client):
    mock_get.return_value = fake_response(404)
    r = client.get("/orders/user/99")
    assert r.status_code == 404


@patch("app.requests.get", side_effect=requests.exceptions.ConnectionError())
def test_orders_by_user_service_down(mock_get, client):
    r = client.get("/orders/user/1")
    assert r.status_code == 503


@patch("app.requests.get")
def test_create_order_ok(mock_get, client):
    mock_get.return_value = fake_response(200, {"id": 1, "active": True})
    r = client.post("/orders", json={"user_id": 1, "product": "Monitor", "total": 300})
    assert r.status_code == 201
    assert r.get_json()["id"] == 4
    assert r.get_json()["quantity"] == 1


def test_create_order_body_not_object(client):
    r = client.post("/orders", json=[1, 2, 3])
    assert r.status_code == 400


def test_create_order_missing_fields(client):
    r = client.post("/orders", json={"user_id": 1})
    assert r.status_code == 400


@patch("app.requests.get")
def test_create_order_user_not_found(mock_get, client):
    mock_get.return_value = fake_response(404)
    r = client.post("/orders", json={"user_id": 99, "product": "X", "total": 10})
    assert r.status_code == 404


@patch("app.requests.get")
def test_create_order_user_inactive(mock_get, client):
    mock_get.return_value = fake_response(200, {"id": 3, "active": False})
    r = client.post("/orders", json={"user_id": 3, "product": "X", "total": 10})
    assert r.status_code == 400


@patch("app.requests.get", side_effect=requests.exceptions.ConnectionError())
def test_create_order_service_down(mock_get, client):
    r = client.post("/orders", json={"user_id": 1, "product": "X", "total": 10})
    assert r.status_code == 503

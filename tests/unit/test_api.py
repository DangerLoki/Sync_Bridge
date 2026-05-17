import pytest
from fastapi.testclient import TestClient

from src.interfaces.api.app import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

def test_health_status_200():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_retorna_ok():
    response = client.get("/health")
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

def test_home_status_200():
    response = client.get("/")
    assert response.status_code == 200


def test_home_retorna_html():
    response = client.get("/")
    assert "text/html" in response.headers["content-type"]


# ---------------------------------------------------------------------------
# POST /transfer — campos obrigatórios ausentes
# ---------------------------------------------------------------------------

def test_transfer_sem_nenhum_campo_retorna_422():
    """FastAPI retorna 422 quando campos Form obrigatórios estão ausentes."""
    response = client.post("/transfer")
    assert response.status_code == 422


def test_transfer_sem_target_type_retorna_422():
    """source_type informado, target_type ausente → ainda 422."""
    response = client.post("/transfer", data={"source_type": "csv"})
    assert response.status_code == 422


def test_transfer_tipo_invalido_retorna_200_com_erro_no_html():
    """Tipo inválido: a app retorna 200 com mensagem de erro embutida no HTML."""
    response = client.post("/transfer", data={
        "source_type": "formato_inexistente",
        "target_type": "csv",
        "source": "qualquer.csv",
        "target": "/tmp/saida.csv",
    })
    assert response.status_code == 200
    assert "Unsupported source type" in response.text


# ---------------------------------------------------------------------------
# GET /browse
# ---------------------------------------------------------------------------

def test_browse_path_default_retorna_200():
    response = client.get("/browse")
    assert response.status_code == 200


def test_browse_path_invalido_retorna_erro():
    """Path inválido: a app retorna 404 com mensagem de erro."""
    response = client.get("/browse", params={"path": "/caminho/que/nao/existe/xyz"})
    assert response.status_code == 404
    assert "error" in response.json()

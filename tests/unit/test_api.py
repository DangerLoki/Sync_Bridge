import os
import tempfile
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.interfaces.api.app import app, build_reader, build_writer

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


def test_browse_permission_error_retorna_lista_vazia(tmp_path):
    """Diretório sem permissão retorna lista vazia sem erro HTTP."""
    restricted = tmp_path / "restricted"
    restricted.mkdir()
    restricted.chmod(0o000)
    try:
        response = client.get("/browse", params={"path": str(restricted)})
        assert response.status_code == 200
        assert response.json()["entries"] == []
    finally:
        restricted.chmod(0o755)


# ---------------------------------------------------------------------------
# build_reader — todos os tipos de conector
# ---------------------------------------------------------------------------

def test_build_reader_csv():
    from src.infrastructure.connectors.csv.csv_reader import CsvReader
    reader = build_reader("csv", table_name="", encoding="utf-8")
    assert isinstance(reader, CsvReader)


def test_build_reader_sqlite():
    from src.infrastructure.connectors.sqlite.sqlite_reader import SqliteReader
    reader = build_reader("sqlite", table_name="mytable")
    assert isinstance(reader, SqliteReader)


def test_build_reader_parquet():
    from src.infrastructure.connectors.parquet.parquet_reader import ParquetReader
    reader = build_reader("parquet", table_name="")
    assert isinstance(reader, ParquetReader)


def test_build_reader_tipo_invalido_levanta_erro():
    with pytest.raises(ValueError, match="Unsupported source type"):
        build_reader("formato_inexistente", table_name="")


def test_build_reader_sqlserver():
    mock_reader_cls = MagicMock()
    mock_module = MagicMock(SqlServerReader=mock_reader_cls)
    with patch.dict("sys.modules", {
        "pyodbc": MagicMock(),
        "src.infrastructure.connectors.sqlserver.sqlserver_reader": mock_module,
    }):
        reader = build_reader("sqlserver", table_name="tabela")
    assert reader is mock_reader_cls.return_value


def test_build_reader_oracle():
    mock_reader_cls = MagicMock()
    mock_module = MagicMock(OracleReader=mock_reader_cls)
    with patch.dict("sys.modules", {
        "oracledb": MagicMock(),
        "src.infrastructure.connectors.oracle.oracle_reader": mock_module,
    }):
        reader = build_reader("oracle", table_name="tabela", oracle_mode="thin")
    assert reader is mock_reader_cls.return_value


def test_build_reader_bigquery():
    mock_reader_cls = MagicMock()
    mock_module = MagicMock(BigQueryReader=mock_reader_cls)
    with patch.dict("sys.modules", {
        "google": MagicMock(),
        "google.cloud": MagicMock(),
        "google.cloud.bigquery": MagicMock(),
        "google.oauth2": MagicMock(),
        "google.oauth2.service_account": MagicMock(),
        "src.infrastructure.connectors.bigquery.bigquery_reader": mock_module,
    }):
        reader = build_reader("bigquery", table_name="dataset.tabela", bq_project_id="proj")
    assert reader is mock_reader_cls.return_value


# ---------------------------------------------------------------------------
# build_writer — todos os tipos de conector
# ---------------------------------------------------------------------------

def test_build_writer_csv():
    from src.infrastructure.connectors.csv.csv_writer import CsvWriter
    writer = build_writer("csv", table_name="", encoding="utf-8")
    assert isinstance(writer, CsvWriter)


def test_build_writer_sqlite():
    from src.infrastructure.connectors.sqlite.sqlite_writer import SqliteWriter
    writer = build_writer("sqlite", table_name="mytable")
    assert isinstance(writer, SqliteWriter)


def test_build_writer_parquet():
    from src.infrastructure.connectors.parquet.parquet_writer import ParquetWriter
    writer = build_writer("parquet", table_name="")
    assert isinstance(writer, ParquetWriter)


def test_build_writer_tipo_invalido_levanta_erro():
    with pytest.raises(ValueError, match="Unsupported target type"):
        build_writer("formato_inexistente", table_name="")


def test_build_writer_sqlserver():
    mock_writer_cls = MagicMock()
    mock_module = MagicMock(SqlServerWriter=mock_writer_cls)
    with patch.dict("sys.modules", {
        "pyodbc": MagicMock(),
        "src.infrastructure.connectors.sqlserver.sqlserver_writer": mock_module,
    }):
        writer = build_writer("sqlserver", table_name="tabela")
    assert writer is mock_writer_cls.return_value


def test_build_writer_oracle():
    mock_writer_cls = MagicMock()
    mock_module = MagicMock(OracleWriter=mock_writer_cls)
    with patch.dict("sys.modules", {
        "oracledb": MagicMock(),
        "src.infrastructure.connectors.oracle.oracle_writer": mock_module,
    }):
        writer = build_writer("oracle", table_name="tabela", oracle_mode="thin")
    assert writer is mock_writer_cls.return_value


def test_build_writer_bigquery():
    mock_writer_cls = MagicMock()
    mock_module = MagicMock(BigQueryWriter=mock_writer_cls)
    with patch.dict("sys.modules", {
        "google": MagicMock(),
        "google.cloud": MagicMock(),
        "google.cloud.bigquery": MagicMock(),
        "google.oauth2": MagicMock(),
        "google.oauth2.service_account": MagicMock(),
        "src.infrastructure.connectors.bigquery.bigquery_writer": mock_module,
    }):
        writer = build_writer("bigquery", table_name="dataset.tabela", bq_project_id="proj")
    assert writer is mock_writer_cls.return_value


# ---------------------------------------------------------------------------
# POST /transfer — validações obrigatórias
# ---------------------------------------------------------------------------

def _post_transfer(**kwargs):
    data = {"source_type": "csv", "target_type": "csv", **kwargs}
    return client.post("/transfer", data=data)


def test_transfer_sqlite_sem_tabela_origem_retorna_erro():
    response = _post_transfer(source_type="sqlite", source="/tmp/x.db")
    assert response.status_code == 200
    assert "obrigatório" in response.text.lower() or "obrigat" in response.text


def test_transfer_sqlite_sem_tabela_destino_retorna_erro():
    response = _post_transfer(target_type="sqlite", target="/tmp/x.db")
    assert response.status_code == 200
    assert "obrigatório" in response.text.lower() or "obrigat" in response.text


def test_transfer_sqlserver_sem_tabela_origem_retorna_erro():
    response = _post_transfer(
        source_type="sqlserver",
        source_connection_string="DSN=teste",
    )
    assert response.status_code == 200
    assert "obrigatório" in response.text.lower() or "obrigat" in response.text


def test_transfer_sqlserver_sem_connection_string_retorna_erro():
    response = _post_transfer(
        source_type="sqlserver",
        source_table_name_sql="tabela",
    )
    assert response.status_code == 200
    assert "obrigatório" in response.text.lower() or "obrigat" in response.text


def test_transfer_oracle_sem_dsn_origem_retorna_erro():
    response = _post_transfer(source_type="oracle", source_table_name_oracle="tab")
    assert response.status_code == 200
    assert "obrigatório" in response.text.lower() or "obrigat" in response.text


def test_transfer_oracle_sem_tabela_origem_retorna_erro():
    response = _post_transfer(source_type="oracle", source_oracle_dsn="user/pass@host/db")
    assert response.status_code == 200
    assert "obrigatório" in response.text.lower() or "obrigat" in response.text


def test_transfer_bigquery_sem_credenciais_origem_retorna_erro():
    response = _post_transfer(source_type="bigquery", source_table_name_bq="ds.tab")
    assert response.status_code == 200
    assert "obrigatório" in response.text.lower() or "obrigat" in response.text


def test_transfer_bigquery_sem_tabela_origem_retorna_erro():
    response = _post_transfer(
        source_type="bigquery",
        source_bq_credentials_file="/tmp/cred.json",
    )
    assert response.status_code == 200
    assert "obrigatório" in response.text.lower() or "obrigat" in response.text


# ---------------------------------------------------------------------------
# POST /transfer — transferência CSV → CSV com sucesso
# ---------------------------------------------------------------------------

def test_transfer_csv_para_csv_sucesso(tmp_path):
    src_file = tmp_path / "entrada.csv"
    dst_file = tmp_path / "saida.csv"
    src_file.write_text("col1,col2\n1,2\n3,4\n", encoding="utf-8-sig")

    response = client.post("/transfer", data={
        "source_type": "csv",
        "target_type": "csv",
        "source": str(src_file),
        "target": str(dst_file),
        "source_sep_file": ",",
        "target_sep_file": ",",
        "source_encoding": "utf-8-sig",
        "target_encoding": "utf-8-sig",
    })
    assert response.status_code == 200
    assert dst_file.exists()


# ---------------------------------------------------------------------------
# POST /test-connection
# ---------------------------------------------------------------------------

def test_test_connection_sucesso():
    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    with patch.dict("sys.modules", {"pyodbc": MagicMock(connect=MagicMock(return_value=mock_conn))}):
        response = client.post("/test-connection", data={"connection_string": "DSN=teste"})
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_test_connection_falha():
    mock_pyodbc = MagicMock()
    mock_pyodbc.connect.side_effect = Exception("Connection refused")
    with patch.dict("sys.modules", {"pyodbc": mock_pyodbc}):
        response = client.post("/test-connection", data={"connection_string": "DSN=invalido"})
    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert "Connection refused" in response.json()["message"]


# ---------------------------------------------------------------------------
# POST /test-connection-oracle
# ---------------------------------------------------------------------------

def test_test_connection_oracle_sucesso():
    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_oracledb = MagicMock()
    mock_oracledb.connect.return_value = mock_conn
    with patch.dict("sys.modules", {"oracledb": mock_oracledb}):
        response = client.post("/test-connection-oracle", data={
            "dsn": "user/pass@host/db", "mode": "thin", "client_lib_dir": ""
        })
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_test_connection_oracle_falha():
    mock_oracledb = MagicMock()
    mock_oracledb.connect.side_effect = Exception("ORA-12154")
    with patch.dict("sys.modules", {"oracledb": mock_oracledb}):
        response = client.post("/test-connection-oracle", data={
            "dsn": "invalido", "mode": "thin", "client_lib_dir": ""
        })
    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert "ORA-12154" in response.json()["message"]


def test_test_connection_oracle_thick_mode():
    """Modo thick chama init_oracle_client antes de conectar."""
    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_oracledb = MagicMock()
    mock_oracledb.connect.return_value = mock_conn
    with patch.dict("sys.modules", {"oracledb": mock_oracledb}):
        response = client.post("/test-connection-oracle", data={
            "dsn": "user/pass@host/db", "mode": "thick", "client_lib_dir": "/opt/oracle"
        })
    assert response.status_code == 200
    assert response.json()["ok"] is True
    mock_oracledb.init_oracle_client.assert_called_once_with(lib_dir="/opt/oracle")


def test_test_connection_oracle_thick_init_ja_inicializado():
    """init_oracle_client levantando exceção não impede a conexão (já inicializado)."""
    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_oracledb = MagicMock()
    mock_oracledb.connect.return_value = mock_conn
    mock_oracledb.init_oracle_client.side_effect = Exception("already initialized")
    with patch.dict("sys.modules", {"oracledb": mock_oracledb}):
        response = client.post("/test-connection-oracle", data={
            "dsn": "user/pass@host/db", "mode": "thick", "client_lib_dir": ""
        })
    assert response.status_code == 200
    assert response.json()["ok"] is True


# ---------------------------------------------------------------------------
# POST /test-connection-bigquery
# ---------------------------------------------------------------------------

def test_test_connection_bigquery_sucesso():
    mock_credentials = MagicMock()
    mock_credentials.project_id = "meu-projeto"
    mock_sa = MagicMock()
    mock_sa.Credentials.from_service_account_file.return_value = mock_credentials
    mock_client = MagicMock()
    mock_client.list_datasets.return_value = iter([])
    mock_bq = MagicMock()
    mock_bq.Client.return_value = mock_client
    mock_google_cloud = MagicMock()
    mock_google_cloud.bigquery = mock_bq
    with patch.dict("sys.modules", {
        "google": MagicMock(),
        "google.cloud": mock_google_cloud,
        "google.cloud.bigquery": mock_bq,
        "google.oauth2": MagicMock(),
        "google.oauth2.service_account": mock_sa,
    }):
        response = client.post("/test-connection-bigquery", data={
            "credentials_file": "/tmp/cred.json",
            "project_id": "meu-projeto",
        })
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert "meu-projeto" in response.json()["message"]


def test_test_connection_bigquery_falha():
    mock_sa = MagicMock()
    mock_sa.Credentials.from_service_account_file.return_value = MagicMock(project_id="p")
    mock_client = MagicMock()
    mock_client.list_datasets.side_effect = Exception("BigQuery unavailable")
    mock_bq = MagicMock()
    mock_bq.Client.return_value = mock_client
    mock_google_cloud = MagicMock()
    mock_google_cloud.bigquery = mock_bq
    with patch.dict("sys.modules", {
        "google": MagicMock(),
        "google.cloud": mock_google_cloud,
        "google.cloud.bigquery": mock_bq,
        "google.oauth2": MagicMock(),
        "google.oauth2.service_account": mock_sa,
    }):
        response = client.post("/test-connection-bigquery", data={
            "credentials_file": "/tmp/inexistente.json",
            "project_id": "",
        })
    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert "BigQuery unavailable" in response.json()["message"]


# ---------------------------------------------------------------------------
# POST /transfer — validações de destino (target_type)
# ---------------------------------------------------------------------------

def test_transfer_sqlite_destino_sem_tabela_retorna_erro():
    response = client.post("/transfer", data={
        "source_type": "csv",
        "target_type": "sqlite",
        "source": "/tmp/x.csv",
        "target": "/tmp/x.db",
    })
    assert response.status_code == 200
    assert "obrigatório" in response.text.lower() or "obrigat" in response.text


def test_transfer_sqlserver_destino_sem_tabela_retorna_erro():
    response = client.post("/transfer", data={
        "source_type": "csv",
        "target_type": "sqlserver",
        "source": "/tmp/x.csv",
        "target_connection_string": "DSN=teste",
    })
    assert response.status_code == 200
    assert "obrigatório" in response.text.lower() or "obrigat" in response.text


def test_transfer_sqlserver_destino_sem_connection_string_retorna_erro():
    response = client.post("/transfer", data={
        "source_type": "csv",
        "target_type": "sqlserver",
        "source": "/tmp/x.csv",
        "target_table_name_sql": "tabela",
    })
    assert response.status_code == 200
    assert "obrigatório" in response.text.lower() or "obrigat" in response.text


def test_transfer_oracle_destino_sem_dsn_retorna_erro():
    response = client.post("/transfer", data={
        "source_type": "csv",
        "target_type": "oracle",
        "source": "/tmp/x.csv",
        "target_table_name_oracle": "tabela",
    })
    assert response.status_code == 200
    assert "obrigatório" in response.text.lower() or "obrigat" in response.text


def test_transfer_oracle_destino_sem_tabela_retorna_erro():
    response = client.post("/transfer", data={
        "source_type": "csv",
        "target_type": "oracle",
        "source": "/tmp/x.csv",
        "target_oracle_dsn": "user/pass@host/db",
    })
    assert response.status_code == 200
    assert "obrigatório" in response.text.lower() or "obrigat" in response.text


def test_transfer_bigquery_destino_sem_credenciais_retorna_erro():
    response = client.post("/transfer", data={
        "source_type": "csv",
        "target_type": "bigquery",
        "source": "/tmp/x.csv",
        "target_table_name_bq": "ds.tab",
    })
    assert response.status_code == 200
    assert "obrigatório" in response.text.lower() or "obrigat" in response.text


def test_transfer_bigquery_destino_sem_tabela_retorna_erro():
    response = client.post("/transfer", data={
        "source_type": "csv",
        "target_type": "bigquery",
        "source": "/tmp/x.csv",
        "target_bq_credentials_file": "/tmp/cred.json",
    })
    assert response.status_code == 200
    assert "obrigatório" in response.text.lower() or "obrigat" in response.text


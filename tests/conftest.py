"""Fixtures compartilhadas entre os testes unitários e de integração."""
from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """DataFrame padrão de 4 linhas usado nos testes."""
    return pd.DataFrame(
        [
            {"id": 1, "name": "Ana", "age": 25, "city": "Sao Paulo"},
            {"id": 2, "name": "Bruno", "age": 31, "city": "Rio de Janeiro"},
            {"id": 3, "name": "Carla", "age": 28, "city": "Belo Horizonte"},
            {"id": 4, "name": "Diego", "age": 35, "city": "Curitiba"},
        ]
    )


@pytest.fixture
def sample_csv(tmp_path: Path, sample_df: pd.DataFrame) -> Path:
    """Cria um arquivo CSV temporário com o sample_df e retorna o caminho."""
    csv_path = tmp_path / "people.csv"
    sample_df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def sample_parquet(tmp_path: Path, sample_df: pd.DataFrame) -> Path:
    """Cria um arquivo Parquet temporário com o sample_df e retorna o caminho."""
    parquet_path = tmp_path / "people.parquet"
    sample_df.to_parquet(parquet_path, index=False)
    return parquet_path


@pytest.fixture
def sample_sqlite(tmp_path: Path, sample_df: pd.DataFrame) -> tuple[Path, str]:
    """Cria um banco SQLite temporário com tabela 'people' e retorna (caminho, tabela)."""
    import sqlite3

    db_path = tmp_path / "people.db"
    with sqlite3.connect(db_path) as conn:
        sample_df.to_sql("people", conn, if_exists="replace", index=False)
    return db_path, "people"

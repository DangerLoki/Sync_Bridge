import logging
from typing import Any, cast

import pandas as pd

from src.domain.exceptions.transfer_exceptions import TargetWriteError
from src.domain.ports.data_writer import DataWriter

logger = logging.getLogger(__name__)

_thick_initialized = False


def _ensure_thick_mode(client_lib_dir: str) -> None:
    """Inicializa o Oracle Client para o modo thick (apenas uma vez por processo)."""
    global _thick_initialized
    if _thick_initialized:
        return
    try:
        import oracledb
        oracledb.init_oracle_client(lib_dir=client_lib_dir or None)
        _thick_initialized = True
        logger.debug("Oracle thick mode inicializado com lib_dir=%r", client_lib_dir or "<padrão>")
    except Exception as exc:
        raise TargetWriteError(
            f"Falha ao inicializar Oracle Client (thick mode): {exc}"
        ) from exc


def _qualify(table_name: str) -> str:
    """Qualifica o nome da tabela/schema com aspas duplas do padrão Oracle."""
    if "." in table_name:
        schema, table = table_name.split(".", 1)
        return f'"{schema}"."{table}"'
    return f'"{table_name}"'


def _oracle_sql_type(dtype) -> str:
    if pd.api.types.is_integer_dtype(dtype):
        return "NUMBER(19)"
    if pd.api.types.is_float_dtype(dtype):
        return "BINARY_DOUBLE"
    if pd.api.types.is_bool_dtype(dtype):
        return "NUMBER(1)"
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "TIMESTAMP"
    return "NVARCHAR2(2000)"


class OracleWriter(DataWriter):
    """Escreve dados em uma tabela Oracle (recria a tabela a cada execução).

    Parâmetros
    ----------
    table_name : str
        Nome da tabela (ou SCHEMA.TABELA).
    mode : {'thin', 'thick'}
        ``thin`` — puro-Python, sem Oracle Client.
        ``thick`` — requer o Oracle Instant Client instalado.
    client_lib_dir : str
        Caminho para o diretório do Oracle Instant Client (obrigatório no modo thick).
    """

    def __init__(
        self,
        table_name: str,
        mode: str = "thin",
        client_lib_dir: str = "",
    ) -> None:
        self.table_name = table_name
        self.mode = mode
        self.client_lib_dir = client_lib_dir

    def write(self, data: pd.DataFrame, target: str, sep_file: str = ",", append: bool = False) -> int:
        """Escreve o DataFrame na tabela Oracle.

        Parameters
        ----------
        target : str
            DSN no formato ``usuario/senha@host:porta/service_name``.
        append : bool
            Quando True, insere os dados sem recriar a tabela.
        """
        """
        try:
            import oracledb
        except ImportError as exc:
            raise TargetWriteError(
                "Pacote 'oracledb' não está instalado. Execute: pip install oracledb"
            ) from exc

        if self.mode == "thick":
            _ensure_thick_mode(self.client_lib_dir)

        qualified = _qualify(self.table_name)

        try:
            logger.debug(
                "Escrevendo %d linhas na tabela Oracle '%s' (mode=%s, append=%s)",
                len(data), self.table_name, self.mode, append,
            )
            with oracledb.connect(target) as conn:
                cursor = conn.cursor()

                if not append:
                    # Drop table if it exists (Oracle < 23c não suporta DROP TABLE IF EXISTS)
                    try:
                        cursor.execute(f"DROP TABLE {qualified} PURGE")
                        logger.debug("Tabela Oracle '%s' removida.", self.table_name)
                    except oracledb.DatabaseError as exc:
                        # ORA-00942: table or view does not exist — ignorar
                        err, = exc.args
                        if err.code != 942:
                            raise

                    # CREATE TABLE com tipos inferidos do DataFrame
                    col_defs = [
                        f'"{col}" {_oracle_sql_type(dtype)}'
                        for col, dtype in data.dtypes.items()
                    ]
                    create_sql = f"CREATE TABLE {qualified} ({', '.join(col_defs)})"
                    cursor.execute(create_sql)

                # INSERT em batch usando bind variables posicionais (:1, :2, ...)
                if not data.empty:
                    placeholders = ", ".join(
                        f":{i + 1}" for i in range(len(data.columns))
                    )
                    insert_sql = f"INSERT INTO {qualified} VALUES ({placeholders})"

                    # Substitui NaN/NaT por None para que o driver envie NULL
                    clean = data.astype(object).where(pd.notna(data),
                                                      other=cast(Any, None))  # type: ignore[assignment]

                    batch_size = 5000
                    rows = [
                        tuple(row) for row in clean.itertuples(index=False, name=None)
                    ]
                    for i in range(0, len(rows), batch_size):
                        cursor.executemany(insert_sql, rows[i : i + batch_size])

                conn.commit()

            logger.debug(
                "Escrita Oracle concluída: tabela '%s'", self.table_name
            )
            return len(data)
        except oracledb.Error as exc:
            logger.error(
                "Falha ao escrever na tabela Oracle '%s': %s", self.table_name, exc
            )
            raise TargetWriteError(
                f"Falha ao escrever dados na tabela Oracle '{self.table_name}': {exc}"
            ) from exc

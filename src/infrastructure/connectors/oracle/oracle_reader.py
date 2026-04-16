import logging

import pandas as pd

from src.domain.exceptions.transfer_exceptions import (
    InvalidSourceError,
    SourceReadError,
)
from src.domain.ports.data_reader import DataReader

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
        raise SourceReadError(
            f"Falha ao inicializar Oracle Client (thick mode): {exc}"
        ) from exc


def _qualify(table_name: str) -> str:
    """Qualifica o nome da tabela/schema com aspas duplas do padrão Oracle."""
    if "." in table_name:
        schema, table = table_name.split(".", 1)
        return f'"{schema}"."{table}"'
    return f'"{table_name}"'


class OracleReader(DataReader):
    """Lê dados de uma tabela Oracle.

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

    def read(self, source: str, sep_file: str = ",", custom_query: str = "") -> pd.DataFrame:
        """Lê a tabela e retorna um DataFrame.

        Parameters
        ----------
        source : str
            DSN no formato ``usuario/senha@host:porta/service_name``
            (ex.: ``scott/tiger@localhost:1521/FREEPDB1``).
        custom_query : str
            Consulta SQL personalizada (opcional). Se informada, substitui o
            ``SELECT *`` padrão.
        """
        if not source:
            raise InvalidSourceError("DSN do Oracle é obrigatório.")

        try:
            import oracledb
        except ImportError as exc:
            raise SourceReadError(
                "Pacote 'oracledb' não está instalado. Execute: pip install oracledb"
            ) from exc

        if self.mode == "thick":
            _ensure_thick_mode(self.client_lib_dir)

        if custom_query.strip():
            query = custom_query.strip()
        else:
            query = f"SELECT * FROM {_qualify(self.table_name)}"

        try:
            logger.debug(
                "Lendo do Oracle (mode=%s) — query: %s", self.mode, query
            )
            with oracledb.connect(source) as conn:
                df = pd.read_sql(query, conn)
            logger.debug(
                "Leitura Oracle concluída: %d linhas", len(df)
            )
            return df
        except oracledb.Error as exc:
            logger.error(
                "Falha ao ler tabela '%s' do Oracle: %s", self.table_name, exc
            )
            raise SourceReadError(
                f"Falha ao ler tabela '{self.table_name}' do Oracle: {exc}"
            ) from exc

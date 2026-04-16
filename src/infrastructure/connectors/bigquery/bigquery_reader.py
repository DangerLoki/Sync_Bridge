import logging

import pandas as pd

from src.domain.exceptions.transfer_exceptions import (
    InvalidSourceError,
    SourceReadError,
)
from src.domain.ports.data_reader import DataReader

logger = logging.getLogger(__name__)


class BigQueryReader(DataReader):
    """Lê dados de uma tabela BigQuery usando um arquivo de credenciais JSON.

    Parâmetros
    ----------
    table_name : str
        Nome no formato ``dataset.tabela`` ou ``projeto.dataset.tabela``.
        Se omitir o projeto, ele é obtido do ``project_id``.
    project_id : str
        ID do projeto GCP (pode ser deixado vazio se já embutido em ``table_name``
        ou presente no arquivo de credenciais).
    """

    def __init__(self, table_name: str, project_id: str = "") -> None:
        self.table_name = table_name
        self.project_id = project_id

    def read(self, source: str, sep_file: str = ",", custom_query: str = "") -> pd.DataFrame:
        """Lê a tabela e retorna um DataFrame.

        Parameters
        ----------
        source : str
            Caminho absoluto para o arquivo de credenciais JSON da conta de serviço.
        custom_query : str
            Consulta SQL personalizada (opcional — BigQuery Standard SQL).
        """
        if not source:
            raise InvalidSourceError(
                "Caminho para o arquivo de credenciais JSON do BigQuery é obrigatório."
            )

        try:
            from google.cloud import bigquery
            from google.oauth2 import service_account
        except ImportError as exc:
            raise SourceReadError(
                "Pacote 'google-cloud-bigquery' não está instalado. "
                "Execute: pip install google-cloud-bigquery db-dtypes"
            ) from exc

        try:
            credentials = service_account.Credentials.from_service_account_file(
                source,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            project = self.project_id or credentials.project_id
            client = bigquery.Client(credentials=credentials, project=project)

            # Monta a referência completa da tabela
            table_ref = self.table_name
            if table_ref.count(".") == 1 and project:
                table_ref = f"{project}.{table_ref}"

            if custom_query.strip():
                query = custom_query.strip()
            else:
                query = f"SELECT * FROM `{table_ref}`"

            logger.debug(
                "Lendo do BigQuery (project=%s) — query: %s", project, query
            )
            df = client.query(query).to_dataframe()
            logger.debug(
                "Leitura BigQuery concluída: %d linhas", len(df)
            )
            return df
        except Exception as exc:
            logger.error("Falha ao ler tabela '%s' do BigQuery: %s", self.table_name, exc)
            raise SourceReadError(
                f"Falha ao ler tabela '{self.table_name}' do BigQuery: {exc}"
            ) from exc

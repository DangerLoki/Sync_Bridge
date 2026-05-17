import logging

import pandas as pd

from src.domain.exceptions.transfer_exceptions import TargetWriteError
from src.domain.ports.data_writer import DataWriter

logger = logging.getLogger(__name__)


class BigQueryWriter(DataWriter):
    """Escreve dados em uma tabela BigQuery (sobrescreve se já existir).

    Parâmetros
    ----------
    table_name : str
        Nome no formato ``dataset.tabela`` ou ``projeto.dataset.tabela``.
    project_id : str
        ID do projeto GCP (pode ser deixado vazio se já embutido em ``table_name``
        ou presente no arquivo de credenciais).
    """

    def __init__(self, table_name: str, project_id: str = "") -> None:
        self.table_name = table_name
        self.project_id = project_id

    def write(self, data: pd.DataFrame, target: str, sep_file: str = ",", append: bool = False) -> int:
        """Escreve o DataFrame na tabela BigQuery.

        Parameters
        ----------
        target : str
            Caminho absoluto para o arquivo de credenciais JSON da conta de serviço.
        append : bool
            Quando True, usa ``WRITE_APPEND`` em vez de ``WRITE_TRUNCATE``.
        """
        try:
            from google.cloud import bigquery
            from google.oauth2 import service_account
        except ImportError as exc:
            raise TargetWriteError(
                "Pacote 'google-cloud-bigquery' não está instalado. "
                "Execute: pip install google-cloud-bigquery db-dtypes"
            ) from exc

        try:
            credentials = service_account.Credentials.from_service_account_file(
                target,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            project = self.project_id or credentials.project_id
            client = bigquery.Client(credentials=credentials, project=project)

            # Monta a referência completa da tabela
            table_ref = self.table_name
            if table_ref.count(".") == 1 and project:
                table_ref = f"{project}.{table_ref}"

            job_config = bigquery.LoadJobConfig(
                write_disposition=(
                    bigquery.WriteDisposition.WRITE_APPEND
                    if append
                    else bigquery.WriteDisposition.WRITE_TRUNCATE
                ),
                autodetect=True,
            )

            logger.debug(
                "Escrevendo %d linhas na tabela BigQuery '%s' (project=%s, append=%s)",
                len(data), table_ref, project, append,
            )
            job = client.load_table_from_dataframe(data, table_ref, job_config=job_config)
            job.result()  # aguarda conclusão

            logger.debug("Escrita BigQuery concluída: tabela '%s'", table_ref)
            return len(data)
        except Exception as exc:
            logger.error(
                "Falha ao escrever na tabela BigQuery '%s': %s", self.table_name, exc
            )
            raise TargetWriteError(
                f"Falha ao escrever dados na tabela BigQuery '{self.table_name}': {exc}"
            ) from exc

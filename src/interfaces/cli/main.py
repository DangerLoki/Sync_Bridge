from src.application.dto.transfer_request import TransferRequest
from src.application.services.transfer_service import TransferService
from src.domain.exceptions.transfer_exceptions import TransferError
from src.infrastructure.connectors.csv.csv_reader import CsvReader
from src.infrastructure.connectors.csv.csv_writer import CsvWriter
from src.infrastructure.connectors.sqlite.sqlite_reader import SqliteReader
from src.infrastructure.connectors.sqlite.sqlite_writer import SqliteWriter


def run_csv_to_sqlite() -> None:
    request = TransferRequest(
        source="sample_data/people.csv",
        target="sample_data/app.db",
    )

    reader = CsvReader()
    writer = SqliteWriter(table_name="people")
    service = TransferService(reader=reader, writer=writer)

    result = service.execute(request)
    print(result)


def run_sqlite_to_csv() -> None:
    request = TransferRequest(
        source="sample_data/app.db",
        target="sample_data/people_exported.csv",
    )

    reader = SqliteReader(table_name="people")
    writer = CsvWriter()
    service = TransferService(reader=reader, writer=writer)

    result = service.execute(request)
    print(result)


def main() -> None:
    try:
        run_csv_to_sqlite()
        run_sqlite_to_csv()
    except TransferError as exc:
        print(f"Transfer failed: {exc}")


if __name__ == "__main__":
    main()
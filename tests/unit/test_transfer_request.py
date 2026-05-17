from src.application.dto.transfer_request import TransferRequest


class TestTransferRequest:
    def test_required_fields_are_set(self):
        request = TransferRequest(source="in.csv", target="out.db")

        assert request.source == "in.csv"
        assert request.target == "out.db"

    def test_default_sep_file(self):
        request = TransferRequest(source="in.csv", target="out.csv")

        assert request.source_sep_file == ","
        assert request.target_sep_file == ","

    def test_default_encoding(self):
        request = TransferRequest(source="in.csv", target="out.csv")

        assert request.source_encoding == "utf-8-sig"
        assert request.target_encoding == "utf-8-sig"

    def test_default_custom_query_is_empty(self):
        request = TransferRequest(source="in.csv", target="out.csv")

        assert request.custom_query == ""

    def test_custom_sep_file(self):
        request = TransferRequest(source="in.csv", target="out.csv", source_sep_file=";", target_sep_file="|")

        assert request.source_sep_file == ";"
        assert request.target_sep_file == "|"

    def test_custom_encoding(self):
        request = TransferRequest(
            source="in.csv",
            target="out.csv",
            source_encoding="latin-1",
            target_encoding="utf-8",
        )

        assert request.source_encoding == "latin-1"
        assert request.target_encoding == "utf-8"

    def test_custom_query(self):
        request = TransferRequest(
            source="in.csv", target="out.csv", custom_query="age > 18"
        )

        assert request.custom_query == "age > 18"

    def test_empty_source_raises_value_error(self):
        import pytest
        with pytest.raises(ValueError, match="source cannot be empty"):
            TransferRequest(source="   ", target="out.csv")

    def test_empty_target_raises_value_error(self):
        import pytest
        with pytest.raises(ValueError, match="target cannot be empty"):
            TransferRequest(source="in.csv", target="   ")

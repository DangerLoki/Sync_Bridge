# Transferência em Chunks (Chunked Transfer)

## O que é?

Por padrão, o Sync Bridge carrega **todos os dados da origem na memória** antes de escrever no destino. Isso funciona bem para arquivos pequenos, mas pode causar estouro de memória em datasets grandes.

O modo **chunked** resolve esse problema lendo e escrevendo os dados em **lotes (chunks)** de N linhas por vez, mantendo apenas um pedaço dos dados em memória a cada iteração.

---

## Como ativar

O campo `chunk_size` no `TransferRequest` controla o comportamento:

| Valor | Comportamento |
|-------|--------------|
| `0` (padrão) | Carrega tudo de uma vez (`_execute_full`) |
| `> 0` | Processa em lotes de `chunk_size` linhas (`_execute_chunked`) |

```python
request = TransferRequest(
    source="dados.csv",
    target="saida.db",
    chunk_size=1000,  # lê e escreve 1000 linhas por vez
)
```

Valor negativo levanta `ValueError`.

---

## Fluxo interno

```
TransferRequest(chunk_size=N)
        │
        ▼
TransferService.execute()
        │
        ├─ chunk_size == 0 ──► _execute_full()
        │                        reader.read() → writer.write()
        │
        └─ chunk_size > 0 ──► _execute_chunked()
                                 reader.read_chunks() → writer.write(append=...)
```

### `_execute_chunked` passo a passo

```python
for chunk_index, chunk in enumerate(reader.read_chunks(source, chunk_size)):
    rows_read += len(chunk)
    writer.write(chunk, target, append=(chunk_index > 0))
    rows_written += written
```

- **Primeiro chunk** (`chunk_index == 0`): `append=False` — cria/sobrescreve o destino.
- **Chunks seguintes** (`chunk_index > 0`): `append=True` — acrescenta ao destino existente.

---

## `DataReader.read_chunks`

Definido em `src/domain/ports/data_reader.py` como método da porta abstrata.

### Implementação padrão (fallback)

Carrega o DataFrame completo via `read()` e fatia com `iloc`:

```python
df = self.read(source, ...)
for start in range(0, len(df), chunk_size):
    yield df.iloc[start : start + chunk_size]
```

Útil para conectores que ainda não têm streaming nativo.

### Implementações nativas (streaming real)

Conectores que sobrescrevem `read_chunks` com streaming de verdade — nunca carregam o arquivo inteiro na memória:

| Conector | Mecanismo |
|----------|-----------|
| `CsvReader` | `pd.read_csv(..., chunksize=N)` |
| `SqliteReader` | `pd.read_sql(..., chunksize=N)` |
| `SqlServerReader` | `pd.read_sql(..., chunksize=N)` via `pyodbc` |
| `OracleReader` | `pd.read_sql(..., chunksize=N)` via `oracledb` |
| `ParquetReader` | usa a implementação padrão (fallback) |

---

## Modo append nos writers

Para que os chunks sejam concatenados corretamente no destino, cada writer suporta o parâmetro `append`:

- **`CsvWriter`**: no primeiro chunk abre o arquivo normalmente; nos seguintes abre em modo `a` (append) sem reescrever o cabeçalho.
- **`SqliteWriter`**: usa `if_exists='replace'` no primeiro e `if_exists='append'` nos seguintes.
- **`ParquetWriter`**: usa `pyarrow.parquet.ParquetWriter` mantendo o arquivo aberto e chamando `write_table()` para cada chunk; fecha o arquivo ao chamar `writer.close()`.

---

## Exemplo completo

```python
from src.application.dto.transfer_request import TransferRequest
from src.application.services.transfer_service import TransferService
from src.infrastructure.connectors.csv.csv_reader import CsvReader
from src.infrastructure.connectors.sqlite.sqlite_writer import SqliteWriter

reader = CsvReader()
writer = SqliteWriter(table_name="pessoas")
service = TransferService(reader=reader, writer=writer)

request = TransferRequest(
    source="dados_grandes.csv",
    target="banco.db",
    chunk_size=5000,  # processa 5000 linhas por vez
)

result = service.execute(request)
print(result)
# Status: SUCCESS | Rows read: 500000 | Rows written: 500000
```

---

## Diagrama de sequência

```
CLI/API           TransferService      CsvReader          SqliteWriter
   │                    │                  │                    │
   │  execute(req)      │                  │                    │
   │──────────────────►│                  │                    │
   │                    │ read_chunks()    │                    │
   │                    │────────────────►│                    │
   │                    │  chunk[0]        │                    │
   │                    │◄────────────────│                    │
   │                    │                  │  write(append=F)   │
   │                    │───────────────────────────────────►  │
   │                    │  chunk[1]        │                    │
   │                    │◄────────────────│                    │
   │                    │                  │  write(append=T)   │
   │                    │───────────────────────────────────►  │
   │                    │  ...             │                    │
   │                    │ close()          │                    │
   │                    │───────────────────────────────────►  │
   │  TransferResult    │                  │                    │
   │◄──────────────────│                  │                    │
```

---

## Onde os testes estão

`tests/unit/test_chunked_transfer.py` cobre:

- Validação do campo `chunk_size` no `TransferRequest`
- Implementação padrão (slice) do `DataReader.read_chunks`
- `CsvReader.read_chunks` nativo
- `SqliteReader.read_chunks` nativo
- Modo append do `CsvWriter` e `SqliteWriter`
- Escrita em chunks do `ParquetWriter`
- Caminho de execução chunked no `TransferService`

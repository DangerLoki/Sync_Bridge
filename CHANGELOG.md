# Changelog

Todas as mudanças notáveis deste projeto estão documentadas aqui.  
O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).

---

## [2.0.0] – 2026-05-18

### Adicionado
- **Terminal de progresso em tempo real** — ao clicar em "Executar transferência" a página exibe um painel terminal dark-mode com logs coloridos por nível, barra de progresso animada e contador de linhas lidas/escritas em tempo real, sem reload de página.
- **Endpoint SSE `POST /transfer/stream`** — transmite eventos de log e progresso via Server-Sent Events enquanto a transferência roda em background thread.
- **`progress_callback` no `TransferService`** — parâmetro opcional chamado a cada chunk (modo chunked) ou ao final da escrita (modo full), emitindo `rows_read`, `rows_written` e `chunk_index`.
- **Binários standalone via PyInstaller** — workflow `release.yml` no GitHub Actions compila executáveis para Linux e Windows sem necessidade de Python instalado.
- **Script `scripts/run_server.py`** — entry point do servidor para build PyInstaller, com detecção automática de caminhos frozen/dev.
- **Correção no `/browse`** — ao receber um caminho de arquivo, navega automaticamente para o diretório pai em vez de lançar `NotADirectoryError`.
- **Logging melhorado no `/browse`** — `PermissionError` e exceções inesperadas agora são registradas e retornadas como JSON em vez de propagar para o Starlette.

### Alterado
- `app.py`: caminhos de templates e arquivos estáticos agora resolvidos via `SYNCBRIDGE_BASE_DIR` (compatível com dev e build PyInstaller).
- `logging_config.py`: removida sobrescrita redundante de `file_handler.suffix` que interferia no `extMatch` interno do `TimedRotatingFileHandler`.
- Imports reorganizados em `app.py` para conformidade com ruff (E401, E402, I001).

---

## [0.2.0] – 2026-05-16

### Adicionado
- **Modo chunked / streaming** — parâmetro `chunk_size` para transferências em lotes sem carregar tudo na memória.
- **Docker** — `Dockerfile`, `docker-compose.yml` e job de CI que testa o container.
- **Rotação diária de logs** com retenção de 30 dias via `TimedRotatingFileHandler`.
- **Conector Oracle** — modos thin e thick, com suporte a Oracle Instant Client.
- **Conector BigQuery** — autenticação via service account JSON.
- **Interface multi-step (stepper)** — wizard Entrada → Saída → Resumo antes de executar.
- **Navegador de arquivos modal** — browse no servidor diretamente pela UI.
- **Botões de teste de conexão** — SQL Server, Oracle e BigQuery.
- **Consulta personalizada** — campo de query customizada para filtrar dados na origem.
- **Seleção de colunas** no `ParquetReader` e `ParquetWriter`.
- **Encoding e compressão configuráveis** para CSV e Parquet.

### Alterado
- Refatoração geral de legibilidade nos conectores e serviços.
- Testes unitários e de integração expandidos para maior cobertura.

---

## [0.1.0] – inicial

### Adicionado
- Conectores CSV, SQLite e Parquet (leitura e escrita).
- Interface web com FastAPI + Jinja2.
- CLI com Typer.
- Arquitetura domain-driven (ports & adapters).
- Logging básico com `logging`.

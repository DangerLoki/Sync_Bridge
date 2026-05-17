# SyncBridge

[![CI](https://github.com/DangerLoki/Sync_Bridge/actions/workflows/ci.yml/badge.svg)](https://github.com/DangerLoki/Sync_Bridge/actions/workflows/ci.yml)

Ferramenta **local** de transferência de dados tabulares entre arquivos e bancos de dados. Roda na máquina do desenvolvedor — não é um serviço de rede exposto, não possui endpoints públicos e não foi projetado para acesso remoto.

## ⚠️ Uso local apenas

Este projeto **não é um serviço web de produção**. A interface web (FastAPI) existe como conveniência para uso local via navegador (`localhost`). O projeto não possui autenticação, controle de acesso ou qualquer mecanismo de segurança para exposição pública. **Não exponha à internet nem utilize em ambientes multiusuário.**

## Objetivo do projeto

O SyncBridge foi criado para praticar e demonstrar uma arquitetura de software mais organizada para movimentação de dados, separando regras de negócio, conectores de infraestrutura e ponto de entrada da aplicação.

O projeto permite:

- transferir dados entre **CSV**, **SQLite**, **Parquet**, **SQL Server**, **Oracle** e **BigQuery**
- configurar separador e encoding dos arquivos CSV
- configurar compressão dos arquivos Parquet (snappy, gzip, brotli, zstd)
- conectar ao SQL Server via connection string (ODBC)
- conectar ao Oracle em modo **Thin** (puro Python) ou **Thick** (Oracle Instant Client)
- conectar ao BigQuery via arquivo de credenciais JSON (Service Account)
- aplicar **consultas/filtros personalizados** na leitura (SQL nativo ou expressão pandas, dependendo da fonte)
- operar via **CLI** ou via **interface web (FastAPI)**
- navegar e selecionar arquivos pelo navegador integrado na interface web
- testar conexões (SQL Server, Oracle, BigQuery) diretamente pela interface
- tratar erros de leitura e escrita com exceções customizadas
- validar o fluxo com testes automatizados

## Funcionalidades atuais

- Transferência entre qualquer combinação de **CSV**, **SQLite**, **Parquet**, **SQL Server**, **Oracle** e **BigQuery**
- Separador de CSV configurável (vírgula, ponto e vírgula, tabulação, pipe)
- Encoding de CSV configurável (padrão `utf-8-sig`)
- Compressão de Parquet configurável na escrita (snappy, gzip, brotli, zstd, nenhuma)
- Conexão ao SQL Server via connection string ODBC com nome de tabela configurável
- Conexão ao Oracle com escolha entre modo **Thin** e **Thick**, com campo para informar o diretório do Oracle Instant Client
- Conexão ao BigQuery via arquivo JSON de Service Account, com Project ID opcional
- **Consulta personalizada (opcional)** — permite filtrar ou transformar os dados na leitura:
  - **Bancos de dados** (SQLite, SQL Server, Oracle, BigQuery): consulta SQL nativa que substitui o `SELECT *` padrão
  - **Arquivos** (CSV, Parquet): expressão `pandas.DataFrame.query()` aplicada após a leitura
- Interface **Web (FastAPI + Jinja2 + Bootstrap 5)** com wizard de 3 etapas (Entrada → Saída → Resumo)
- Navegador de arquivos do servidor integrado à interface web
- Botão de **testar conexão** para SQL Server, Oracle e BigQuery
- Campos condicionais por tipo de origem/destino
- Placeholder e dicas dinâmicas no campo de consulta, adaptados à linguagem da fonte selecionada
- Interface **CLI** com fluxos de demonstração pré-configurados
- Estrutura em camadas com conectores desacoplados por interfaces (Ports and Adapters)
- Tratamento de erros com exceções customizadas
- **Logging** com rotação de arquivo (`logs/sync_bridge.log`, máx. 5 MB, 3 backups)
- **Testes unitários** para domínio, DTO, serviço e conectores (CSV, SQLite, Parquet) com mocks
- **Testes de integração** end-to-end entre os conectores com `pytest`

## Conectores disponíveis

| Conector       | Leitura | Escrita | Configurações                                                        |
|----------------|---------|---------|----------------------------------------------------------------------|
| **CSV**        | ✅      | ✅      | Separador, Encoding                                                   |
| **SQLite**     | ✅      | ✅      | Nome da tabela                                                        |
| **Parquet**    | ✅      | ✅      | Compressão (escrita)                                                  |
| **SQL Server** | ✅      | ✅      | Connection string (ODBC), Nome da tabela                              |
| **Oracle**     | ✅      | ✅      | DSN, Nome da tabela, Modo (Thin / Thick), Diretório do Instant Client |
| **BigQuery**   | ✅      | ✅      | Arquivo JSON de credenciais, Project ID, Nome da tabela (dataset.tabela) |

## Consulta personalizada

O campo de consulta personalizada é **opcional** e aparece em um painel colapsável no passo de Entrada. Quando preenchido, altera a forma como os dados são lidos:

| Fonte                              | Linguagem              | Exemplo                                                  |
|------------------------------------|------------------------|----------------------------------------------------------|
| CSV / Parquet                      | `pandas.DataFrame.query()` | `idade > 30 and cidade == "SP"`                         |
| SQLite                             | SQL (SQLite)           | `SELECT * FROM people WHERE age > 30`                    |
| SQL Server                         | T-SQL                  | `SELECT * FROM [dbo].[people] WHERE age > 30`            |
| Oracle                             | Oracle SQL             | `SELECT * FROM "SCHEMA"."TABELA" WHERE ROWNUM <= 1000`   |
| BigQuery                           | Standard SQL           | `` SELECT * FROM `projeto.dataset.tabela` WHERE data > "2024-01-01" `` |

Quando o campo fica vazio, o comportamento padrão é mantido (`SELECT *` ou leitura completa do arquivo).

## Estrutura do projeto

```text
src/
  core/
    logging_config.py
  domain/
    ports/
    models/
    exceptions/
  application/
    services/
    dto/
  infrastructure/
    connectors/
      csv/
      sqlite/
      parquet/
      sqlserver/
      oracle/
      bigquery/
  interfaces/
    cli/
    api/
      app.py
      templates/
      static/
      image/

tests/
  unit/
    connectors/
      test_csv_reader.py
      test_csv_writer.py
      test_sqlite_reader.py
      test_sqlite_writer.py
      test_parquet_reader.py
      test_parquet_writer.py
    test_transfer_exceptions.py
    test_transfer_request.py
    test_transfer_result.py
    test_transfer_service.py
  integration/
    test_transfer_flow.py

sample_data/
logs/
Dockerfile
docker-compose.yml
.dockerignore
```

## Arquitetura

O projeto segue uma abordagem de **arquitetura modular em camadas**, inspirada no conceito de **Ports and Adapters**.

### Camadas

* **core**: configurações transversais (ex: logging)
* **domain**: contratos (`DataReader`, `DataWriter`), modelos e exceções da aplicação
* **application**: serviços responsáveis pelos casos de uso (`TransferService`)
* **infrastructure**: implementações concretas dos conectores (CSV, SQLite, Parquet, SQL Server, Oracle, BigQuery)
* **interfaces**: pontos de entrada da aplicação (CLI e API web)

Essa estrutura facilita a evolução do projeto para novos conectores no futuro, como por exemplo PostgreSQL, Excel, MySQL ou outros formatos.

## Tecnologias utilizadas

* **Python**
* **Pandas** — manipulação de dados tabulares
* **FastAPI** + **Uvicorn** — API e servidor web
* **Jinja2** — templates HTML
* **Bootstrap 5** — interface web responsiva
* **PyArrow** — leitura e escrita de Parquet
* **pyodbc** — conexão com SQL Server via ODBC
* **oracledb** — conexão com Oracle (modo Thin puro-Python ou Thick com Instant Client)
* **google-cloud-bigquery** + **db-dtypes** — conexão com BigQuery via API
* **SQLite** (stdlib) — banco de dados local
* **Pytest** — testes automatizados
* **pytest-cov** — cobertura de testes (integrado ao CI)
* **httpx** — cliente HTTP usado pelo `TestClient` do FastAPI nos testes de API
* **Typer** — framework para CLI com argumentos de linha de comando
* **ruff** — linter e formatador de código (usado no CI)
* **mypy** — verificação estática de tipos (usado no CI)
* **pandas-stubs** — stubs de tipos para pandas (usado com mypy)
* **uv** — gerenciador de pacotes e lockfile (alternativa rápida ao pip)
* **Docker** — containerização da aplicação (API e CLI)
* **GitHub Actions** — CI com testes, lint e validação do container Docker

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/DangerLoki/Sync_Bridge.git
cd Sync_Bridge
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
.venv\Scripts\activate      # Windows
```

### 3. Instale as dependências

Instalação básica (CSV, SQLite, interface web e CLI):

```bash
pip install -e .
```

Com suporte a Parquet:

```bash
pip install -e ".[parquet]"
```

Com dependências de desenvolvimento (testes, type checking):

```bash
pip install -e ".[dev,parquet,api]"
```

> **Alternativa com uv** (mais rápido):
> ```bash
> pip install uv
> uv pip install -e ".[dev,parquet,api]"
> ```
> O projeto inclui `uv.lock` para instalação reproduzível:
> ```bash
> uv sync --extra dev --extra parquet --extra api
> ```

### 4. Verifique a instalação rodando os testes

```bash
python -m pytest -q
```

---

## Como executar

### Interface Web

```bash
uvicorn src.interfaces.api.app:app --reload
```

Acesse `http://localhost:8000` no navegador para usar o wizard de transferência.

O endpoint `GET /health` retorna o status da aplicação.

### Rodando com docker-compose

A forma mais simples de subir a interface web é via `docker-compose`. O arquivo `docker-compose.yml` já configura a porta, os volumes e o healthcheck.

```bash
docker compose up --build
```

Acesse `http://localhost:8000` após o container subir.

Para parar:

```bash
docker compose down
```

O volume `./logs` é mapeado automaticamente, mantendo os logs persistidos no host.

### Rodando com Docker

O projeto inclui um `Dockerfile` multi-stage com dois targets: `api` e `cli`.

**API:**

```bash
docker build --target api -t sync-bridge-api .
docker run -p 8000:8000 \
  -v ./sample_data:/app/sample_data \
  -v ./logs:/app/logs \
  sync-bridge-api
```

Acesse `http://localhost:8000` após o container subir.

**CLI:**

```bash
docker build --target cli -t sync-bridge-cli .

# Ver ajuda
docker run --rm sync-bridge-cli --help

# Fluxo de demonstração
docker run --rm -v ./sample_data:/app/sample_data sync-bridge-cli demo

# Transferência manual
docker run --rm -v ./sample_data:/app/sample_data sync-bridge-cli transfer \
  sample_data/people.csv sample_data/out.db --source-type csv --target-type sqlite --table people
```

> **Volumes:** os arquivos CSV, SQLite e Parquet precisam estar acessíveis dentro do container. Use `-v ./sample_data:/app/sample_data` para mapear a pasta do host.

### CLI

A partir da raiz do projeto:

```bash
# Comando de transferência com argumentos
python -m src.interfaces.cli.main transfer data.csv saida.db --source-type csv --target-type sqlite --table people

# Estratégia de escrita
python -m src.interfaces.cli.main transfer origem.csv destino.db --source-type csv --target-type sqlite --if-exists append

# Ver ajuda
python -m src.interfaces.cli.main --help
python -m src.interfaces.cli.main transfer --help

# Fluxos de demonstração pré-configurados
python -m src.interfaces.cli.main demo
```

## Como rodar os testes

Rodar todos os testes:

```bash
pytest -q
```

Apenas testes unitários:

```bash
pytest tests/unit/ -v
```

Apenas testes de integração:

```bash
pytest tests/integration/ -v
```

### Cobertura dos testes

| Módulo | Tipo | O que é testado |
|--------|------|-----------------|
| `TransferResult` | Unitário | Atributos, `__repr__`, `__str__`, status |
| `TransferRequest` | Unitário | Defaults, campos customizados |
| Exceções de domínio | Unitário | Hierarquia, mensagens, captura como `TransferError` |
| `TransferService` | Unitário | Resultado, propagação de erros, repasse de argumentos (com mocks) |
| `CsvReader` / `CsvWriter` | Unitário | Leitura, escrita, separador, encoding, query filter, erros |
| `SqliteReader` / `SqliteWriter` | Unitário | Leitura, escrita, query SQL, tabela ausente, replace |
| `ParquetReader` / `ParquetWriter` | Unitário | Leitura, escrita, compressão, arquivo corrompido, query filter |
| Fluxos CSV ↔ SQLite ↔ Parquet | Integração | Transferências end-to-end com verificação dos dados escritos |

## Exemplo de fluxo (interface web)

1. **Entrada** — Selecione o tipo de origem (CSV, SQLite, Parquet, SQL Server, Oracle ou BigQuery), informe o caminho/connection string/DSN/credenciais, configure os parâmetros específicos e, opcionalmente, escreva uma consulta personalizada
2. **Saída** — Selecione o tipo de destino e configure os parâmetros de escrita
3. **Resumo** — Revise a configuração (incluindo a consulta, se houver) e execute a transferência
4. **Resultado** — Veja o status, quantidade de linhas lidas e escritas

## Tratamento de erros

O projeto possui tratamento para cenários como:

* arquivo de origem inexistente
* caminho de origem/destino inválido
* falha ao ler tabela (SQLite, SQL Server, Oracle ou BigQuery)
* falha ao escrever no destino
* nome da tabela, connection string, DSN ou arquivo de credenciais não informados
* falha na inicialização do Oracle Instant Client (modo Thick)
* tipo de conector não suportado
* consulta personalizada inválida

## Logging

Os logs são gravados simultaneamente no console e no arquivo `logs/sync_bridge.log`, com **rotação diária à meia-noite** (mantém os últimos 30 dias).

Arquivos rotacionados recebem o sufixo da data: `sync_bridge.log.2026-05-16`

Formato: `%(asctime)s | %(levelname)-8s | %(name)s | %(message)s`

## Pré-requisitos por conector

### SQL Server

É necessário ter um **ODBC Driver** instalado na máquina (ex: `ODBC Driver 17 for SQL Server` ou `ODBC Driver 18 for SQL Server`).

Exemplo de connection string:

```
DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=mydb;Trusted_Connection=yes;
```

### Oracle

- **Modo Thin** (padrão): não requer instalação extra — puro Python.
- **Modo Thick**: requer o [Oracle Instant Client](https://www.oracle.com/database/technologies/instant-client.html) instalado. Informe o caminho do diretório na interface ou configure a variável de ambiente `LD_LIBRARY_PATH`.

Exemplo de DSN:

```
scott/tiger@localhost:1521/FREEPDB1
```

### BigQuery

É necessário um arquivo JSON de **Service Account** com permissões de leitura/escrita no BigQuery. O Project ID pode ser informado manualmente ou é lido automaticamente do JSON.

Instale as dependências:

```bash
pip install -e ".[bigquery]"
```

## O que este projeto demonstra

* organização de projeto Python
* separação de responsabilidades
* arquitetura em camadas (Ports and Adapters)
* abstração de conectores com interfaces
* manipulação de dados tabulares com pandas
* leitura e escrita entre múltiplos formatos e bancos de dados (CSV, SQLite, Parquet, SQL Server, Oracle, BigQuery)
* consulta personalizada na leitura (SQL nativo ou expressão pandas)
* tratamento de erros com exceções customizadas
* logging com rotação diária de arquivos
* API REST com FastAPI
* interface web moderna com Bootstrap 5 e wizard interativo
* testes automatizados com pytest (unitários com mocks + integração end-to-end)
* containerização com Docker (multi-stage build para API e CLI)
* CI/CD com GitHub Actions (testes, lint, mypy e validação do container Docker)

## Limitações atuais

* **projeto para uso local apenas** — sem autenticação, autorização ou proteção contra acesso externo
* estratégia de escrita configurável (`replace` ou `append`) implementada no SQLite; SQL Server e Oracle permanecem fixos em `replace`
* CLI cobre apenas conectores locais (CSV, SQLite, Parquet); SQL Server, Oracle e BigQuery só pela interface web
* conector SQL Server requer ODBC Driver instalado na máquina
* conector Oracle em modo Thick requer Oracle Instant Client instalado
* conector BigQuery requer arquivo de credenciais JSON e acesso à API do Google Cloud

## Próximos passos

* expandir conectores (ex: Excel, PostgreSQL, MySQL)
* evoluir a estrutura de configuração da transferência

## Motivação

A proposta deste projeto não é competir com ferramentas consolidadas de mercado, mas sim servir como uma base modular e testável para fluxos de movimentação de dados, com foco em aprendizado, evolução arquitetural e demonstração técnica em portfólio.
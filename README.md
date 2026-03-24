# SyncBridge

Ferramenta modular para transferência de dados tabulares entre arquivos e bancos de dados, com foco em arquitetura em camadas, abstração de conectores e fluxos reproduzíveis.

## Objetivo do projeto

O SyncBridge foi criado para praticar e demonstrar uma arquitetura de software mais organizada para movimentação de dados, separando regras de negócio, conectores de infraestrutura e ponto de entrada da aplicação.

O projeto permite:

- transferir dados entre **CSV**, **SQLite**, **Parquet** e **SQL Server**
- configurar separador e encoding dos arquivos CSV
- configurar compressão dos arquivos Parquet (snappy, gzip, brotli, zstd)
- conectar ao SQL Server via connection string (ODBC)
- operar via **CLI** ou via **interface web (FastAPI)**
- navegar e selecionar arquivos pelo navegador integrado na interface web
- tratar erros de leitura e escrita com exceções customizadas
- validar o fluxo com testes automatizados

## Funcionalidades atuais

- Transferência entre qualquer combinação de **CSV**, **SQLite**, **Parquet** e **SQL Server**
- Separador de CSV configurável (vírgula, ponto e vírgula, tabulação, pipe)
- Encoding de CSV configurável (padrão `utf-8-sig`)
- Compressão de Parquet configurável na escrita (snappy, gzip, brotli, zstd, nenhuma)
- Conexão ao SQL Server via connection string ODBC com nome de tabela configurável
- Interface **Web (FastAPI + Jinja2 + Bootstrap 5)** com wizard de 3 etapas (Entrada → Saída → Resumo)
- Navegador de arquivos do servidor integrado à interface web
- Campos condicionais por tipo de origem/destino
- Interface **CLI** com fluxos de demonstração pré-configurados
- Estrutura em camadas com conectores desacoplados por interfaces (Ports and Adapters)
- Tratamento de erros com exceções customizadas
- **Logging** com rotação de arquivo (`logs/sync_bridge.log`, máx. 5 MB, 3 backups)
- Testes de integração com `pytest`

## Conectores disponíveis

| Conector     | Leitura | Escrita | Configurações                          |
|--------------|---------|---------|----------------------------------------|
| **CSV**      | ✅      | ✅      | Separador, Encoding                    |
| **SQLite**   | ✅      | ✅      | Nome da tabela                         |
| **Parquet**  | ✅      | ✅      | Compressão (escrita)                   |
| **SQL Server** | ✅    | ✅      | Connection string (ODBC), Nome da tabela |

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
  interfaces/
    cli/
    api/
      app.py
      templates/
      static/
      image/

tests/
  integration/

sample_data/
logs/
```

## Arquitetura

O projeto segue uma abordagem de **arquitetura modular em camadas**, inspirada no conceito de **Ports and Adapters**.

### Camadas

* **core**: configurações transversais (ex: logging)
* **domain**: contratos (`DataReader`, `DataWriter`), modelos e exceções da aplicação
* **application**: serviços responsáveis pelos casos de uso (`TransferService`)
* **infrastructure**: implementações concretas dos conectores (CSV, SQLite, Parquet, SQL Server)
* **interfaces**: pontos de entrada da aplicação (CLI e API web)

Essa estrutura facilita a evolução do projeto para novos conectores no futuro, como por exemplo BigQuery, PostgreSQL, Excel ou outros formatos.

## Tecnologias utilizadas

* **Python**
* **Pandas** — manipulação de dados tabulares
* **FastAPI** + **Uvicorn** — API e servidor web
* **Jinja2** — templates HTML
* **Bootstrap 5** — interface web responsiva
* **PyArrow** — leitura e escrita de Parquet
* **pyodbc** — conexão com SQL Server via ODBC
* **SQLite** (stdlib) — banco de dados local
* **Pytest** — testes automatizados

## Como executar

### Interface Web

```bash
uvicorn src.interfaces.api.app:app --reload
```

Acesse `http://localhost:8000` no navegador para usar o wizard de transferência.

O endpoint `GET /health` retorna o status da aplicação.

### CLI

A partir da raiz do projeto:

```bash
python -m src.interfaces.cli.main
```

A CLI possui fluxos de demonstração pré-configurados (CSV ↔ SQLite, CSV ↔ Parquet).

## Como rodar os testes

```bash
pytest -q
```

## Exemplo de fluxo (interface web)

1. **Entrada** — Selecione o tipo de origem (CSV, SQLite, Parquet ou SQL Server), informe o caminho ou connection string, e configure os parâmetros específicos
2. **Saída** — Selecione o tipo de destino e configure os parâmetros de escrita
3. **Resumo** — Revise a configuração e execute a transferência
4. **Resultado** — Veja o status, quantidade de linhas lidas e escritas

## Tratamento de erros

O projeto possui tratamento para cenários como:

* arquivo de origem inexistente
* caminho de origem/destino inválido
* falha ao ler tabela (SQLite ou SQL Server)
* falha ao escrever no destino
* nome da tabela ou connection string não informados
* tipo de conector não suportado

## Logging

Os logs são gravados simultaneamente no console e no arquivo `logs/sync_bridge.log`, com rotação automática a cada 5 MB (até 3 arquivos de backup).

Formato: `%(asctime)s | %(levelname)-8s | %(name)s | %(message)s`

## Pré-requisitos para SQL Server

Para utilizar o conector SQL Server, é necessário ter um **ODBC Driver** instalado na máquina (ex: `ODBC Driver 17 for SQL Server` ou `ODBC Driver 18 for SQL Server`).

Exemplo de connection string:

```
DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=mydb;Trusted_Connection=yes;
```

## O que este projeto demonstra

* organização de projeto Python
* separação de responsabilidades
* arquitetura em camadas (Ports and Adapters)
* abstração de conectores com interfaces
* manipulação de dados tabulares com pandas
* leitura e escrita entre múltiplos formatos e bancos de dados
* tratamento de erros com exceções customizadas
* logging com rotação de arquivos
* API REST com FastAPI
* interface web moderna com Bootstrap 5 e wizard interativo
* testes automatizados com pytest

## Limitações atuais

* estratégia de escrita no SQLite e SQL Server fixa em `replace` (substitui a tabela)
* CLI sem parâmetros de linha de comando (configuração por código)
* conector SQL Server requer ODBC Driver instalado na máquina

## Próximos passos

* adicionar argumentos de linha de comando na CLI (`argparse` ou `typer`)
* suportar estratégias de escrita como `append`
* expandir conectores (ex: Excel, PostgreSQL, BigQuery)
* evoluir a estrutura de configuração da transferência

## Motivação

A proposta deste projeto não é competir com ferramentas consolidadas de mercado, mas sim servir como uma base modular e testável para fluxos de movimentação de dados, com foco em aprendizado, evolução arquitetural e demonstração técnica em portfólio.
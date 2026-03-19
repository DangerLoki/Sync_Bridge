# SyncBridge

Ferramenta modular para transferência de dados tabulares entre arquivos e bancos locais, com foco em arquitetura em camadas, abstração de conectores e fluxos reproduzíveis.

## Objetivo do projeto

O SyncBridge foi criado para praticar e demonstrar uma arquitetura de software mais organizada para movimentação de dados, separando regras de negócio, conectores de infraestrutura e ponto de entrada da aplicação.

O projeto permite:

- importar dados de **CSV para SQLite**
- exportar dados de **SQLite para CSV**
- configurar o separador do arquivo CSV
- operar via **CLI** ou via **interface web (FastAPI)**
- tratar erros de leitura e escrita com exceções customizadas
- validar o fluxo com testes automatizados

## Funcionalidades atuais

- Transferência de **CSV -> SQLite**
- Transferência de **SQLite -> CSV**
- Separador de CSV configurável via parâmetro `sep_file`
- Estrutura em camadas
- Conectores desacoplados por interfaces
- Tratamento de erros com exceções customizadas
- Interface **CLI** para execução direta
- Interface **Web (FastAPI + Jinja2)** com formulário interativo
- **Logging** com rotação de arquivo (`logs/sync_bridge.log`, máx. 5 MB, 3 backups)
- Testes de integração com `pytest`

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
* **domain**: contratos, modelos e exceções da aplicação
* **application**: serviços responsáveis pelos casos de uso
* **infrastructure**: implementações concretas dos conectores
* **interfaces**: pontos de entrada da aplicação (CLI e API web)

Essa estrutura facilita a evolução do projeto para novos conectores no futuro, como por exemplo BigQuery, SQL Server ou outros formatos de arquivo.

## Tecnologias utilizadas

* **Python**
* **Pandas**
* **SQLite**
* **FastAPI** + **Uvicorn**
* **Jinja2**
* **Pytest**

## Como executar

### CLI

A partir da raiz do projeto:

```bash
python -m src.interfaces.cli.main
```

### Interface Web

```bash
uvicorn src.interfaces.api.app:app --reload
```

Acesse `http://localhost:8000` no navegador para usar o formulário de transferência.

O endpoint `GET /health` retorna o status da aplicação.

## Como rodar os testes

```bash
pytest -q
```

## Exemplo de fluxo

1. Leitura de um arquivo CSV de exemplo
2. Escrita dos dados em uma tabela SQLite
3. Leitura dos dados do SQLite
4. Exportação de volta para CSV

## Tratamento de erros

O projeto possui tratamento para cenários como:

* arquivo CSV inexistente
* caminho de origem inválido
* extensão de arquivo não suportada
* falha ao ler tabela SQLite
* falha ao escrever no destino

## Logging

Os logs são gravados simultaneamente no console e no arquivo `logs/sync_bridge.log`, com rotação automática a cada 5 MB (até 3 arquivos de backup).

## O que este projeto demonstra

Este projeto foi desenvolvido para demonstrar conhecimentos em:

* organização de projeto Python
* separação de responsabilidades
* arquitetura em camadas (Ports and Adapters)
* abstração de conectores
* manipulação de dados tabulares
* leitura e escrita entre diferentes formatos
* tratamento de erros com exceções customizadas
* logging com rotação de arquivos
* API REST com FastAPI
* interface web com Jinja2
* testes automatizados

## Limitações atuais

* suporte apenas a **CSV** e **SQLite**
* estratégia de escrita no SQLite fixa em `replace`
* CLI sem parâmetros de linha de comando (configuração por código)

## Próximos passos

* adicionar argumentos de linha de comando na CLI (`argparse` ou `typer`)
* suportar estratégias de escrita como `append`
* expandir conectores (ex: Excel, PostgreSQL)
* evoluir a estrutura de configuração da transferência

## Motivação

A proposta deste projeto não é competir com ferramentas consolidadas de mercado, mas sim servir como uma base modular e testável para fluxos de movimentação de dados, com foco em aprendizado, evolução arquitetural e demonstração técnica em portfólio.
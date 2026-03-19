# SyncBridge

Ferramenta modular para transferência de dados tabulares entre arquivos e bancos locais, com foco em arquitetura em camadas, abstração de conectores e fluxos reproduzíveis.

## Objetivo do projeto

O SyncBridge foi criado para praticar e demonstrar uma arquitetura de software mais organizada para movimentação de dados, separando regras de negócio, conectores de infraestrutura e ponto de entrada da aplicação.

Nesta versão inicial, o projeto permite:

- importar dados de **CSV para SQLite**
- exportar dados de **SQLite para CSV**
- tratar erros básicos de leitura e escrita
- validar o fluxo com testes automatizados

## Funcionalidades atuais

- Transferência de **CSV -> SQLite**
- Transferência de **SQLite -> CSV**
- Estrutura em camadas
- Conectores desacoplados por interfaces
- Tratamento básico de erros com exceções customizadas
- Testes de integração com `pytest`

## Estrutura do projeto

```text
src/
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

tests/
  integration/

sample_data/

## Arquitetura

O projeto segue uma abordagem de **arquitetura modular em camadas**, inspirada no conceito de **Ports and Adapters**.

### Camadas

* **domain**: contratos, modelos e exceções da aplicação
* **application**: serviços responsáveis pelos casos de uso
* **infrastructure**: implementações concretas dos conectores
* **interfaces**: ponto de entrada da aplicação

Essa estrutura facilita a evolução do projeto para novos conectores no futuro, como por exemplo BigQuery, SQL Server ou outros formatos de arquivo.

## Tecnologias utilizadas

* **Python**
* **Pandas**
* **SQLite**
* **Pytest**

## Como executar

A partir da raiz do projeto:

```bash
python -m src.interfaces.cli.main
```

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

O projeto possui tratamento básico para cenários como:

* arquivo CSV inexistente
* caminho de origem inválido
* falha ao ler tabela SQLite
* falha ao escrever no destino

## O que este projeto demonstra

Este projeto foi desenvolvido para demonstrar conhecimentos em:

* organização de projeto Python
* separação de responsabilidades
* arquitetura em camadas
* abstração de conectores
* manipulação de dados tabulares
* leitura e escrita entre diferentes formatos
* tratamento de erros
* testes automatizados

## Limitações atuais

* suporte apenas a **CSV** e **SQLite**
* interface ainda baseada em execução simples via CLI
* estratégia de escrita no SQLite ainda fixa
* logging ainda não implementado

## Próximos passos

* adicionar parâmetros de linha de comando
* implementar logging
* suportar estratégias como `replace` e `append`
* expandir conectores
* evoluir a estrutura de configuração da transferência

## Motivação

A proposta deste projeto não é competir com ferramentas consolidadas de mercado, mas sim servir como uma base modular e testável para fluxos de movimentação de dados, com foco em aprendizado, evolução arquitetural e demonstração técnica em portfólio.
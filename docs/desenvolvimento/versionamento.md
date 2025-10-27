# 📜 Estratégia de Versionamento Semântico (SemVer)

Este documento detalha a estratégia de versionamento semântico para o SisCoE, adaptada para atender aos rigorosos requisitos de compliance, auditoria e criticidade de um sistema de gestão de efetivo militar.

## 🎯 Visão Geral

O versionamento semântico (SemVer) é um conjunto de regras que dita como os números de versão são atribuídos e incrementados. No contexto do SisCoE, ele não apenas comunica a natureza das mudanças, mas também serve como um pilar para a governança de dados e conformidade legal.

A estrutura de versão adotada é: `MAJOR.MINOR.PATCH`.

### Formato da Versão: `MAJOR.MINOR.PATCH`

- **MAJOR**: Incrementado para mudanças que quebram a compatibilidade da API, a estrutura legal dos dados ou os requisitos de compliance. Essas são mudanças que exigem atenção máxima durante a atualização.
- **MINOR**: Incrementado para adição de novas funcionalidades de forma retrocompatível. O sistema expande suas capacidades sem invalidar o que já existe.
- **PATCH**: Incrementado para correções de bugs e falhas de segurança que são retrocompatíveis. Essencial para garantir a estabilidade e a segurança dos dados críticos.

Adicionalmente, metadados de build podem ser adicionados com um `+`, como `1.0.0+202310231400.a1b2c3d`.

- **Build Metadata**: Contém informações como timestamp do deploy, hash do commit Git e ambiente de destino (e.g., `dev`, `staging`, `prod`). Não indica precedência de versão.

## 🏛️ Definição de Mudanças

### `MAJOR` - Mudanças de Quebra de Conformidade

Exemplos:
- Alteração na estrutura de um campo que armazena um dado pessoal regulado por lei (e.g., formato do RE, CPF).
- Modificação em um fluxo de trabalho que impacta um requisito de auditoria legal.
- Remoção de um endpoint de API usado por sistemas integrados.
- Atualização de uma regra de negócio que altera a forma como a situação funcional de um militar é calculada, se isso tiver implicação legal.

**Impacto**: Exige planejamento cuidadoso, comunicação com stakeholders e, possivelmente, um processo de migração de dados.

### `MINOR` - Novas Funcionalidades

Exemplos:
- Adição de um novo relatório de efetivo.
- Criação de um novo dashboard de BI.
- Inclusão de novos campos não-obrigatórios em um modelo.
- Exposição de um novo endpoint de API para consulta de dados.

**Impacto**: Permite a evolução contínua do sistema com baixo risco de regressão.

### `PATCH` - Correções Críticas

Exemplos:
- Correção de uma vulnerabilidade de segurança (e.g., SQL Injection, XSS).
- Ajuste em um cálculo que produzia resultados incorretos, mas sem impacto legal.
- Correção de um bug na interface que impedia o cadastro de um militar.
- Otimização de uma query lenta que não altera a lógica de negócio.

**Impacto**: Essencial para a manutenção da saúde e segurança do sistema. Devem ser aplicados com agilidade.

## ⚙️ Implementação no Fluxo de Trabalho Git

O versionamento será gerenciado através de tags no Git e um arquivo `CHANGELOG.md`.

1.  **Branching Model**: Recomenda-se o uso de um modelo como o GitFlow (`main`, `develop`, `feature/*`, `release/*`, `hotfix/*`).
2.  **Tags Git**: Cada release no branch `main` deve ser marcada com uma tag de versão anotada.
    ```bash
    # Exemplo de criação de tag para um release minor
    git tag -a v1.2.0 -m "Release 1.2.0: Adiciona funcionalidade de relatórios customizados"
    ```
3.  **Changelog**: Todas as mudanças devem ser documentadas no arquivo `CHANGELOG.md`, seguindo o padrão "Keep a Changelog". Isso cria um histórico legível por humanos das mudanças em cada versão.

### Exemplo de `CHANGELOG.md`

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2023-10-23

### Added
- Funcionalidade de geração de relatórios customizados.
- Novo endpoint `/api/v1/efetivo/estatisticas`.

### Changed
- Melhoria na performance da listagem de militares.

## [1.1.1] - 2023-10-15

### Fixed
- Correção em bug crítico que permitia cadastro de RE duplicado.

## [1.1.0] - 2023-10-10

### Added
- Módulo de gestão de afastamentos.

## [1.0.0] - 2023-09-01

### Added
- Lançamento inicial do SisCoE.
```

## 🤖 Automação

Para garantir a consistência, o processo de versionamento e geração de changelog pode ser automatizado com ferramentas como:

-   **Conventional Commits**: Um padrão de mensagens de commit que permite a automação da determinação da versão e do changelog.
-   **standard-version** (ou similar): Uma ferramenta que lê os commits, determina a próxima versão, cria a tag e atualiza o `CHANGELOG.md` automaticamente.

A adoção desta estratégia de versionamento garante um controle de mudanças robusto, essencial para a governança, segurança e conformidade do SisCoE.

# 📜 Estratégia de Versionamento Semântico (SemVer)

Este documento detalha a estratégia de versionamento semântico para o SisCoE, que é totalmente automatizada usando GitHub Actions e Conventional Commits para garantir consistência, rastreabilidade e conformidade.

## 🎯 Visão Geral

O versionamento semântico (SemVer) é um conjunto de regras que dita como os números de versão são atribuídos e incrementados. No contexto do SisCoE, ele não apenas comunica a natureza das mudanças, mas também serve como um pilar para a governança de dados e conformidade.

A estrutura de versão adotada é: `MAJOR.MINOR.PATCH`.

### Formato da Versão: `MAJOR.MINOR.PATCH`

- **MAJOR**: Incrementado para mudanças que quebram a compatibilidade da API, a estrutura legal dos dados ou os requisitos de compliance. Essas são mudanças que exigem atenção máxima durante a atualização.
- **MINOR**: Incrementado para adição de novas funcionalidades de forma retrocompatível. O sistema expande suas capacidades sem invalidar o que já existe.
- **PATCH**: Incrementado para correções de bugs e falhas de segurança que são retrocompatíveis. Essencial para garantir a estabilidade e a segurança dos dados críticos.

## 🤖 Implementação e Automação com GitHub Actions

O processo de versionamento é 100% automatizado. A fonte da verdade para a versão atual do sistema é o arquivo `VERSION` localizado na raiz do projeto.

O fluxo funciona da seguinte maneira:

1.  **Conventional Commits**: O desenvolvedor deve escrever mensagens de commit seguindo o padrão [Conventional Commits](https://www.conventionalcommits.org/). O tipo de commit (`feat`, `fix`, etc.) é fundamental para o processo.

2.  **Push na Branch Principal**: A cada `push` ou `merge` nas branches `main` ou `master`, o workflow do GitHub Actions em `.github/workflows/versioning.yml` é acionado.

3.  **Execução do Workflow**: A pipeline executa os seguintes passos:
    - **Checkout do Código**: Clona o repositório.
    - **Instalação de Dependências**: Instala a biblioteca `semver`.
    - **Execução do Script de Versionamento**: Roda o script `scripts/bump_version.py`.

4.  **Lógica do Script (`bump_version.py`)**:
    - O script lê a versão atual do arquivo `VERSION`.
    - Ele analisa a mensagem do último commit para determinar o tipo de mudança.
    - Com base no tipo, ele incrementa a versão:
        - `feat:` na mensagem → incrementa **MINOR** (ex: `1.2.0` → `1.3.0`)
        - `fix:` ou `refactor:` na mensagem → incrementa **PATCH** (ex: `1.2.0` → `1.2.1`)
        - `BREAKING CHANGE:` no corpo do commit → incrementa **MAJOR** (ex: `1.2.0` → `2.0.0`)
    - Por fim, o script sobrescreve o arquivo `VERSION` com o novo número.

5.  **Commit e Tag**: Após a execução do script, o workflow do GitHub Actions:
    - Cria um novo commit com a mensagem `chore(release): vX.Y.Z` contendo o arquivo `VERSION` atualizado.
    - Cria e empurra uma nova tag Git (ex: `v1.3.0`) para o repositório.

### Exemplo de Mensagem de Commit

```bash
# Para incrementar a versão MINOR
git commit -m "feat(efetivo): adiciona campo de certificações no perfil"

# Para incrementar a versão PATCH
git commit -m "fix(accounts): corrige bug no fluxo de reset de senha"

# Para incrementar a versão MAJOR
git commit -m "refactor(core): reestrutura models de dados

BREAKING CHANGE: O modelo UserProfile foi removido e substituído pelo modelo Profile."
```

## 🖥️ Exibição da Versão na Aplicação

Para garantir que a versão atual seja sempre visível aos usuários e administradores, um `context_processor` do Django foi implementado.

-   **Arquivo**: `backend/core/context_processors.py`
-   **Função**: `version_context_processor`

Esta função lê o conteúdo do arquivo `VERSION` e injeta a variável `APP_VERSION` em todos os templates do Django. A versão é então exibida no rodapé da página principal.

```html
<!-- Exemplo no template -->
<small>Versão {{ APP_VERSION }}</small>
```

Esta abordagem garante um ciclo de vida de desenvolvimento robusto, onde o versionamento é consistente, automático e diretamente ligado às mudanças realizadas no código.

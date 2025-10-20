# App: Calculadora

O app `calculadora` é uma ferramenta utilitária projetada para uma finalidade muito específica: **calcular o tempo de serviço e as projeções de aposentadoria** de um militar, com base em regras de transição e pedágios, provavelmente decorrentes de uma reforma legislativa.

Ele encapsula uma lógica de negócio complexa, permitindo que os usuários insiram seus dados e recebam uma estimativa de quando atingirão os requisitos para a inatividade.

---

## Como Usar a Calculadora

A calculadora possui uma interface simples com um único formulário. Para obter as projeções, o usuário deve preencher os seguintes campos:

-   **Data de Admissão do Militar**: A data em que o militar ingressou na corporação.
-   **Averbação FFAA/PM/CBM (dias)**: O tempo de serviço prestado em outras Forças Armadas, Polícias Militares ou Corpos de Bombeiros Militares que foi oficialmente averbado (em dias).
-   **Averbação INSS/Outros Órgãos (dias)**: O tempo de contribuição ao INSS ou outros órgãos públicos que foi averbado. O sistema limita este valor a um máximo de 1825 dias (5 anos).
-   **Afastamentos Descontáveis (dias)**: O total de dias de afastamentos que não contam para o tempo de serviço (ex: licenças específicas).

Após preencher os dados e submeter o formulário, a página exibirá os resultados dos cálculos.

---

## Entendendo os Resultados

A view `calcular_tempo_servico` retorna um conjunto de datas e valores projetados. Aqui está o que cada um significa:

-   **Tempo até 01/01/2021**: O total de dias de serviço que o militar possuía na data de corte da reforma (01 de janeiro de 2021).
-   **Pedágio de 17%**: Com base no tempo que faltava para o militar completar 30 anos de serviço na data de corte, o sistema calcula um "pedágio" de 17% que deve ser cumprido. Este valor é exibido em dias.
-   **Data com Pedágio de 17%**: A data projetada em que o militar completará os 30 anos de serviço mais o pedágio de 17%.
-   **Data de 25 Anos de Serviço**: A data em que o militar completa 25 anos de serviço.
-   **Acréscimo de 4 meses**: Um cálculo que adiciona 120 dias (4 meses) para cada ano de serviço a partir de 2022, até um limite.
-   **Data com Tempo Militar**: A data projetada para aposentadoria considerando a regra de 25 anos de serviço mais o acréscimo de 4 meses por ano.

---

## Implementação

O app utiliza um modelo `CalculoMilitar` não para armazenamento persistente, mas como uma estrutura para validar e transportar os dados de entrada do formulário para a view. Toda a lógica de negócio reside na view `calcular_tempo_servico`, que processa os inputs e renderiza os resultados no template `calculadora/calculo.html`.
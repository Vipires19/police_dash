# DEJEM Allocation Engine
## Arquitetura do Motor de Distribuição de Vagas

**Projeto:** Pelotão System

**Versão:** 1.0

**Status:** Draft

---

# 1. Objetivo

O DEJEM Allocation Engine é o responsável por realizar a distribuição justa das vagas disponibilizadas para a Companhia de Força Tática.

Sua única responsabilidade é responder à seguinte pergunta:

> Dada uma quantidade de vagas disponíveis e uma lista de policiais interessados, quantos créditos cada policial deverá receber?

O motor **não cria escalas**, **não escolhe dias** e **não realiza publicações operacionais**.

Essas responsabilidades pertencem ao módulo de Escalas DEJEM.

---

# 2. Filosofia

A campanha DEJEM permanece ativa durante todo o mês.

Enquanto estiver ativa, novas vagas podem surgir, policiais podem alterar seu interesse, cancelar escalas ou solicitar participação.

O Allocation Engine deve reagir a esses eventos mantendo a distribuição justa e auditável.

O motor nunca deve recalcular toda a campanha quando uma alteração puder ser tratada incrementalmente.

---

# 3. Conceitos do Domínio

## Campanha

Representa o mês vigente da DEJEM.

Exemplo:

Julho/2026

Uma campanha possui:

- período
- status
- oferta de vagas
- interessados
- créditos distribuídos

---

## Oferta

Representa a quantidade total de créditos disponíveis para distribuição.

A oferta pode sofrer alterações durante o mês.

Exemplo.

01/07

+100 créditos

08/07

+10 créditos

15/07

-2 créditos

A oferta é cumulativa.

---

## Demanda

Representa a quantidade desejada por cada policial.

Exemplo.

Jorge deseja:

10

Lima deseja:

3

Felipe deseja:

4

A demanda pode ser alterada enquanto a campanha estiver aberta.

---

## Crédito

Representa uma vaga efetivamente atribuída a um policial.

O crédito pertence sempre a uma campanha.

Posteriormente ele poderá ser utilizado na montagem da escala.

O crédito é a ligação entre o Allocation Engine e o módulo de Escalas.

---

# 4. Estados da Campanha

ABERTA

↓

Recebendo interesses.

---

DISTRIBUÍDA

↓

Distribuição inicial concluída.

---

EM ANDAMENTO

↓

Permite novas vagas, cancelamentos e redistribuições.

---

ENCERRADA

↓

Não permite alterações.

---

# 5. Estados do Crédito

Disponível

↓

Agendado

↓

Executado

ou

Disponível

↓

Agendado

↓

Cancelado

↓

Disponível novamente

ou

Disponível

↓

Transferido

↓

Agendado

---

# 6. Dados de cada policial

Cada policial possui os seguintes indicadores.

Desejado

Quantidade solicitada.

Recebido

Quantidade de créditos atribuídos.

Agendado

Créditos já utilizados na escala.

Executado

Créditos efetivamente cumpridos.

Cancelado

Créditos cancelados.

Disponível

Créditos livres para utilização.

Demanda pendente

Desejado - Recebido

---

# 7. Algoritmo de Distribuição Inicial

Entrada.

Oferta

100 créditos.

Demandas.

Jorge

10

Lima

3

Felipe

4

Ângelo

10

O algoritmo deve.

1. Calcular a divisão igualitária.

2. Distribuir igualmente.

3. Distribuir sobras respeitando a antiguidade.

4. Nunca distribuir acima da demanda desejada.

Resultado.

Cada policial recebe apenas o necessário para atender sua solicitação.

---

# 8. Redistribuição Incremental

Sempre que houver alteração na oferta ou demanda.

O motor calcula apenas os policiais que ainda possuem demanda pendente.

Demanda pendente = Desejado - Recebido

Exemplo.

Jorge.

Desejado

10

Recebido

7

Demanda pendente

3

Lima.

Desejado

3

Recebido

3

Demanda pendente

0

Somente Jorge participa da nova redistribuição.

---

# 9. Eventos da Campanha

Toda alteração da campanha deve ser registrada como um evento.

Eventos previstos.

CampaignCreated

OfferAdded

OfferRemoved

InterestRegistered

InterestUpdated

InterestCancelled

CreditsAllocated

CreditScheduled

CreditCancelled

CreditTransferred

CreditExecuted

CampaignClosed

Esses eventos alimentam o histórico da campanha.

---

# 10. Oferta

A oferta pode variar durante todo o mês.

Exemplos.

Chegada de novas vagas.

Cancelamento de vagas.

Convocação extraordinária.

Todas essas alterações modificam apenas a oferta.

---

# 11. Demanda

A demanda também pode variar.

Exemplos.

Policial decide participar após a distribuição.

Policial aumenta a quantidade desejada.

Policial reduz sua participação.

Policial cancela completamente sua inscrição.

Todas essas alterações modificam apenas a demanda.

---

# 12. Fila de Demanda

Quando não houver créditos suficientes.

O policial permanece com demanda pendente.

Exemplo.

Desejado

10

Recebido

7

Pendência

3

Sempre que novas vagas surgirem.

O Allocation Engine deverá atender prioritariamente os policiais que ainda possuem demanda pendente.

---

# 13. Redistribuição Extraordinária

Caso toda a demanda tenha sido atendida e ainda existam créditos disponíveis.

O sistema deverá solicitar uma decisão administrativa.

Opções.

Abrir nova rodada de interesse.

Distribuição manual.

Convocação extraordinária.

O Allocation Engine não deve decidir automaticamente nesses casos.

---

# 14. Auditoria

Toda distribuição deve registrar.

Data.

Oferta existente.

Demandas consideradas.

Critério aplicado.

Créditos distribuídos.

Usuário responsável.

Origem da redistribuição.

Nunca alterar registros históricos.

Toda alteração deve gerar novos eventos.

---

# 15. Integração com Escalas

O Allocation Engine não monta escalas.

Após a distribuição.

Cada policial possuirá um saldo de créditos disponíveis.

O módulo de Escalas consumirá esses créditos conforme os dias forem sendo atribuídos.

Quando uma escala for criada.

Um crédito disponível torna-se agendado.

Quando a escala for executada.

O crédito torna-se executado.

Caso a escala seja cancelada.

O crédito retorna para disponível, permitindo nova utilização.

---

# 16. Casos de Uso

## Caso 1

100 vagas.

132 solicitadas.

Resultado.

Distribuição parcial respeitando igualdade e antiguidade.

---

## Caso 2

Chegam 15 novas vagas.

Resultado.

Atender apenas policiais com demanda pendente.

---

## Caso 3

Policial solicita participação após a distribuição.

Resultado.

Caso exista oferta disponível.

Recebe créditos.

Caso contrário.

Permanece na fila de demanda.

---

## Caso 4

Policial cancela uma escala.

Resultado.

O crédito retorna para disponível.

O crédito poderá ser reutilizado posteriormente.

---

## Caso 5

Sobraram créditos após atender toda a demanda.

Resultado.

O sistema solicita decisão administrativa para distribuição extraordinária.

---

# 17. Princípios do Motor

- O Allocation Engine distribui créditos, nunca escalas.
- O motor trabalha sobre oferta e demanda.
- Toda alteração gera um evento.
- O histórico nunca é perdido.
- Redistribuições são incrementais.
- O algoritmo deve ser justo, auditável e previsível.
- Exceções administrativas permanecem sob responsabilidade do comandante.

# 18. Invariantes do Allocation Engine

São regras que nunca podem ser violadas, independentemente das funcionalidades futuras.

Por exemplo:

Um policial nunca pode receber mais créditos do que solicitou durante a distribuição automática.
Um crédito pertence a uma única campanha.
Um crédito nunca pode estar em dois estados ao mesmo tempo.
Nenhuma redistribuição pode alterar o histórico de distribuições anteriores; ela apenas cria novas alocações.
A soma dos créditos distribuídos nunca pode exceder a oferta disponível.
O módulo de Escalas nunca cria créditos; ele apenas consome créditos distribuídos pelo Allocation Engine.
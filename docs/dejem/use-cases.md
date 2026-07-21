UC01

Criar campanha.

Ator.

Administrador.

Fluxo.

Informa mês.

↓

Sistema cria campanha.

↓

Status OPEN.
UC02

Registrar interesse.

Fluxo.

Policial informa quantidade.

↓

Sistema grava demanda.
UC03

Alterar interesse.

Permitido apenas enquanto a campanha estiver aberta.

UC04

Encerrar inscrições.

Fluxo.

Administrador encerra.

↓

Não aceita novos interesses.

↓

Pronto para distribuir.
UC05

Distribuição inicial.

Fluxo.

Carrega oferta.

↓

Carrega demandas.

↓

Executa algoritmo.

↓

Cria Allocation.

↓

Cria Credits.
UC06

Adicionar vagas.

Fluxo.

Registrar OfferEvent.

↓

Executar redistribuição.

↓

Criar novos créditos.
UC07

Cancelar crédito.

Fluxo.

Cancelar escala.

↓

Crédito volta para AVAILABLE.

↓

Executar redistribuição.
UC08

Novo interessado.

Fluxo.

Registrar Interest.

↓

Existe oferta?

↓

Sim

↓

Distribuir.

↓

Não

↓

Fila.
UC09

Encerrar campanha.

Fluxo.

Status CLOSED.

↓

Nenhuma alteração permitida.
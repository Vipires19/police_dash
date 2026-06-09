# Pelotão System - Fase 1 - Veículos Produtos de Crime

## 1) Contexto da tarefa

Você é um desenvolvedor full-stack sênior especializado em FastAPI, React, TypeScript, PostgreSQL e sistemas operacionais internos.

Estamos trabalhando no projeto já existente "Pelotão System".

Leia integralmente o README do projeto antes de iniciar qualquer alteração.

Objetivo desta tarefa:

Implementar um novo módulo operacional chamado:

Operacional → Veículos Produtos de Crime

O objetivo é substituir o controle manual realizado atualmente em folhas físicas "0 a 9", utilizadas para acompanhamento de veículos produtos de furto e roubo.

IMPORTANTE:

A funcionalidade deve seguir a arquitetura já existente do projeto.

Não criar um novo sistema.

Não refatorar módulos já estáveis.

Alterar apenas o necessário para implementar a funcionalidade.

---

## 2) Contexto operacional

Atualmente o pelotão utiliza uma folha física chamada "0 a 9".

Os veículos são agrupados conforme o primeiro número presente na placa.

Exemplos:

FWB0F63 → Grupo 0

QSY1H54 → Grupo 1

STR3C00 → Grupo 3

Cada grupo possui espaço para 10 veículos.

A folha deve sempre exibir apenas os 10 registros mais recentes de cada grupo.

Quando um 11º veículo for cadastrado:

* O mais antigo deixa de aparecer na folha
* Continua armazenado no banco
* Continua disponível para pesquisa

---

## 3) Regra de negócio

Existem dois conceitos diferentes:

### Histórico

Todos os veículos cadastrados permanecem armazenados.

Nenhum registro deve ser excluído automaticamente.

### Folha Operacional

A folha exibe apenas:

* veículos não localizados
* os 10 registros mais recentes de cada grupo (0 a 9)

---

## 4) Estrutura do menu

Adicionar na sidebar:

Operacional
└── Veículos Produtos de Crime

Ao acessar:

Criar navegação interna contendo:

* Cadastro
* Folha 0 a 9
* Consulta

Pode ser implementado inicialmente por tabs.

---

## 5) Cadastro de veículos

Criar formulário contendo:

Tipo:

* CARRO
* MOTO

Placa

Veículo

Cor

Ano

Natureza:

* FURTO
* ROUBO

Observação (opcional)

Ao salvar:

Identificar automaticamente o primeiro número encontrado na placa.

Exemplos:

FWB0F63 → grupo 0

QSY1H54 → grupo 1

STR3C00 → grupo 3

Armazenar esse valor no banco.

Não solicitar esse campo ao usuário.

---

## 6) Banco de dados

Criar nova tabela:

stolen_vehicles

Campos:

id

vehicle_type
(CARRO | MOTO)

plate

vehicle_model

color

year

occurrence_type
(FURTO | ROUBO)

plate_group
(0 a 9)

observation

is_recovered
(boolean)

recovered_at
(nullable)

created_at

created_by_id

Criar migration Alembic.

Seguir padrão utilizado atualmente no projeto.

---

## 7) Consulta

Criar tela de pesquisa.

Permitir busca por:

* placa
* veículo/modelo
* cor

Exemplos:

Pesquisa:
CG

Resultado esperado:

CG Vermelha 2026 AAA1234

CG Azul 2025 BBB5678

CG Preta 2024 CCC9999

Exibir também:

* tipo
* furto/roubo
* localizado ou não

---

## 8) Localização de veículo

Na tela de consulta deve existir ação:

Marcar como localizado

Ao executar:

is_recovered = true

recovered_at = data/hora atual

Consequências:

* permanece no histórico
* continua pesquisável
* deixa de aparecer automaticamente na Folha 0 a 9

Não excluir registros.

---

## 9) Folha 0 a 9

Criar página operacional inspirada na folha física utilizada pelo pelotão.

Requisitos:

* grupos de 0 a 9
* 10 posições por grupo
* exibir:

  * placa
  * veículo
  * cor
  * ano
  * F ou R

Filtrar apenas:

is_recovered = false

Ordenar:

mais recente → mais antigo

Exibir apenas os 10 registros mais recentes de cada grupo.

---

## 10) Impressão

Implementar inicialmente usando HTML + CSS.

Não utilizar geração PDF nesta fase.

Criar botão:

Imprimir Folha

Ao imprimir:

Gerar duas páginas A4:

Página 1:
CARROS

Página 2:
MOTOS

Cada página deve conter:

0 a 9

10 posições por grupo

Layout otimizado para impressão.

Utilizar CSS @media print.

Objetivo:

Permitir impressão imediata para uso operacional.

---

## 11) Backend

Criar:

Models

Schemas

Services

Routes

Seguindo exatamente o padrão arquitetural existente.

Endpoints mínimos:

POST /stolen-vehicles

GET /stolen-vehicles

GET /stolen-vehicles/search

PATCH /stolen-vehicles/{id}/recover

GET /stolen-vehicles/sheet

---

## 12) Frontend

Criar:

Página operacional

Serviços API

Types

Componentes reutilizáveis

Seguir:

* tema dark atual
* identidade visual existente
* padrão de código já utilizado no projeto

Não introduzir novas bibliotecas sem necessidade.

---

## 13) Restrições

NÃO modificar:

* módulo de escalas
* módulo de férias
* módulo de folgas
* módulo de efetivo
* módulo de viaturas

Apenas integrar o novo módulo ao menu operacional.

---

## 14) Playwright

NÃO executar testes Playwright.

O MCP do Playwright encontra-se indisponível.

Ignorar completamente testes E2E nesta tarefa.

---

## 15) Context7

Utilizar obrigatoriamente Context7 MCP.

Se o Context7 não estiver disponível:

Responder apenas:

"Context7 MCP não disponível. Não posso continuar."

Antes de gerar código mostrar:

Docs consultados

Arquivos que serão alterados

Plano de implementação

Somente depois iniciar as alterações.

---

## 16) Resultado esperado

Ao finalizar:

Fornecer:

* resumo das alterações
* migrations criadas
* endpoints criados
* componentes criados
* arquivos modificados
* comandos necessários para executar migrations
* possíveis melhorias para Fase 2

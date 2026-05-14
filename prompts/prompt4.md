# Estrutura de Prompt — Módulo de Folgas Operacionais (Pelotão System)

## 1) Contexto da tarefa

Você é um(a) desenvolvedor(a) full-stack sênior especializado(a) em sistemas operacionais web modernos.

Estamos evoluindo o projeto já existente chamado:

“Pelotão System”

Stack atual:

* Backend FastAPI
* Frontend React + TypeScript
* PostgreSQL
* Docker Compose
* TailwindCSS

O sistema já possui:

* JWT Auth
* RBAC
* Dashboard operacional
* Efetivo
* Viaturas
* Logs operacionais
* Controle de usuários
* Ordem de antiguidade por display_order

Objetivo desta tarefa:
Criar o módulo operacional de FOLGAS.

O sistema NÃO deve funcionar como um simples CRUD de calendário.

A lógica deve refletir regras operacionais reais de um pelotão policial.

---

## 2) Contexto de tom

Direto, técnico, operacional e enxuto.

Evite:

* overengineering
* abstrações desnecessárias
* bibliotecas excessivas

Explique apenas:

* estrutura criada
* comandos necessários
* arquivos principais
* regras implementadas

---

## 3) Contexto obrigatório de documentação

Você TEM acesso aos MCPs do CursorIDE e DEVE obrigatoriamente utilizar:

* Context7 MCP

Regra crítica:

* Caso o Context7 MCP não esteja disponível:
  responda APENAS:
  “Context7 MCP não disponível. Não posso continuar.”

Antes de gerar código MOSTRE:

* “Docs consultados”
* páginas utilizadas
* snippets curtos usados como base

Consultar documentação atualizada de:

* FastAPI
* SQLAlchemy
* Alembic
* React
* TypeScript
* TailwindCSS
* bibliotecas de calendário utilizadas

---

## 4) Objetivo funcional do módulo

Criar um sistema operacional de:

* solicitação de folgas
* compensações operacionais
* aprovação
* auditoria
* visualização em calendário

O sistema deve possuir:

* Calendário mensal operacional
* Solicitação de folga
* Compensações operacionais
* Aprovação de compensações
* Aprovação de folgas
* Sistema de prioridade operacional
* Sistema de review automático
* Auditoria de decisões

---

# REGRAS OPERACIONAIS

## Limite operacional

Todo policial possui direito padrão de:

* 1 folga mensal

Além disso:

* pode conquistar compensações operacionais

---

## Regra de quantidade mensal

Até:

* 2 folgas totais no mês

Status:

* PENDING

Acima de:

* 2 folgas no mês

Status:

* REVIEW

Motivo:

* excedeu limite operacional mensal

Mesmo em REVIEW:

* o comando ainda pode aprovar

O sistema NÃO deve bloquear automaticamente.

---

## Regra de quantidade diária

Até:

* 4 policiais no mesmo dia

Status:

* PENDING

Acima de:

* 4 policiais no mesmo dia

Status:

* REVIEW

Motivo:

* efetivo reduzido

---

## Prioridade operacional

Folga mensal possui prioridade MAIOR que compensação.

Ordem:

1. Mensal
2. Compensação

Exemplo:

* 4 mensais
* 1 compensação

A compensação deve possuir menor prioridade operacional.

---

## Critério de antiguidade

O sistema já possui:

* display_order
* ordenação operacional do efetivo

O policial:

* mais abaixo no display_order
  é considerado:
* mais recruta

Critério:

* mais antigo possui prioridade operacional

---

# TIPOS DE FOLGA

## Mensal

* padrão
* 1 por mês

---

## Compensação

Conquistada operacionalmente.

O policial NÃO cria diretamente uma folga compensação disponível.

Primeiro:

* cria-se um evento operacional

Após aprovação:

* o sistema gera compensações individuais para os envolvidos.

---

# EVENTOS DE COMPENSAÇÃO

Tipos permitidos:

* CPJ_SUPPORT
* WEAPON_OCCURRENCE
* RELEVANT_OCCURRENCE
* TWO_WANTED
* FIVE_FLAGRANTS

---

# REGRAS DOS EVENTOS

## CPJ_SUPPORT

Critério:

* 04 horas passadas na CPJ ou apoio operacional necessário

---

## WEAPON_OCCURRENCE

Ocorrência com armas.

---

## RELEVANT_OCCURRENCE

Ocorrência de grande relevância.

Sempre:

* deve passar por avaliação do TAT_CMD/N90.

---

## TWO_WANTED

02 procurados.

Campo motivo deve permitir:

* descrição livre
* BOPM
* BOPC

Exemplo:
“02 procurados - BOPM XXXX BOPC XXXX / BOPM XXXX BOPC XXXX”

---

## FIVE_FLAGRANTS

05 flagrantes.

Campo motivo:

* descrição operacional
* BOPMs
* BOPCs

---

# FLUXO DAS COMPENSAÇÕES

## Criação do evento

Pode criar:

* ADMIN
* N90
* TAT_CMD
* BRACAL

Fluxo:

1. Usuário cria evento
2. Seleciona envolvidos
3. Evento vai para aprovação
4. Após aprovação:
   gerar compensação individual para cada policial envolvido

Exemplo:

* João
* Caio
* Campos

Todos recebem:

* 1 compensação disponível

---

# STATUS DAS COMPENSAÇÕES

## Evento operacional

* PENDING
* APPROVED
* REJECTED

---

## Compensação individual

* AVAILABLE
* USED

Quando utilizada:

* não pode mais ser reutilizada

Não possui expiração por tempo.

---

# FLUXO DAS FOLGAS

## Solicitação

Usuário:

* seleciona dia no calendário
* escolhe:

  * mensal
  * compensação disponível

---

# STATUS DAS FOLGAS

* PENDING
* REVIEW
* APPROVED
* REJECTED
* CANCELLED

---

# CORES OPERACIONAIS

Calendário deve possuir indicadores visuais discretos:

* Azul:
  PENDING

* Amarelo:
  REVIEW

* Verde:
  APPROVED

* Vermelho:
  REJECTED

Visual:

* operacional
* minimalista
* tema dark
* estilo tático/policial

Evitar:

* visual colorido estilo SaaS

---

# REGRAS IMPORTANTES

## NÃO bloquear automaticamente

Mesmo:

* acima de 4 policiais
* acima de 2 folgas

o sistema:

* NÃO deve impedir solicitação

Deve apenas:

* marcar como REVIEW
* recomendar análise do comando

---

## NÃO aprovar automaticamente

Toda folga:

* precisa aprovação

Toda compensação:

* precisa aprovação

---

# AUDITORIA

Registrar:

* quem aprovou
* quem rejeitou
* data
* motivo
* alterações

Criar logs operacionais completos.

---

# DASHBOARD

Adicionar:

* folgas pendentes
* compensações pendentes
* dias com efetivo crítico

---

# FRONTEND

Criar páginas:

* /folgas
* /admin/folgas
* /admin/compensacoes

Funcionalidades:

* calendário mensal
* modal de solicitação
* modal de criação de compensação
* visualização de status
* painel de aprovação
* badges operacionais

---

# BACKEND

Criar:

## Models

* LeaveRequest
* CompensationEvent
* UserCompensation
* LeaveApprovalLog

## Enums

* LeaveType
* LeaveStatus
* CompensationType
* CompensationStatus

## Services

* leave_service
* compensation_service

## Rotas mínimas

### Folgas

* GET /leaves/calendar
* POST /leaves/request
* PATCH /leaves/{id}/approve
* PATCH /leaves/{id}/reject
* PATCH /leaves/{id}/cancel

### Compensações

* POST /compensations
* GET /compensations/pending
* PATCH /compensations/{id}/approve
* PATCH /compensations/{id}/reject

---

# Banco de dados

Utilizar:

* SQLAlchemy 2.0
* Alembic
* PostgreSQL

Criar migrations organizadas.

---

# Frontend obrigatório

* React + TypeScript
* TailwindCSS
* Tema dark operacional
* Responsivo
* Layout consistente com sistema atual

---

# Estrutura esperada

Backend:

* /models
* /routes
* /schemas
* /services

Frontend:

* /pages
* /components/folgas
* /services

---

# Regras técnicas

* Corrigir imports automaticamente
* Não gerar arquivos desnecessários
* Utilizar tipagem forte
* Utilizar boas práticas
* Código limpo e modular
* Compatível com arquitetura atual do projeto

---

# 5) Pensar passo a passo internamente

Pense passo a passo internamente para evitar:

* conflitos de migrations
* problemas de RBAC
* erros de calendário
* erros de timezone
* erros de validação
* conflitos de lógica operacional

NÃO mostre seu raciocínio.

Mostre apenas:

* resultado final
* estrutura criada
* comandos necessários

---

# 6) Formatação obrigatória da saída

Responda EXATAMENTE nesta ordem:

1. Verificação do Context7
2. Docs consultados
3. Dependências instaladas
4. Estrutura criada
5. Models criados
6. Enums criados
7. Rotas criadas
8. Regras operacionais implementadas
9. Variáveis de ambiente necessárias
10. Passo a passo dos comandos
11. Melhorias futuras

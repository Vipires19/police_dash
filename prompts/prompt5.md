# Estrutura de Prompt (Nova funcionalidade: módulo de Férias e LP)

## 1) Contexto da tarefa

Você é um(a) desenvolvedor(a) full-stack sênior especializado(a) em sistemas operacionais web modernos.

Estamos evoluindo o projeto já existente chamado **Pelotão System**, um sistema operacional interno para um pelotão policial utilizando:

* FastAPI
* React + TypeScript
* PostgreSQL
* Docker
* TailwindCSS

O sistema já possui:

* autenticação JWT
* RBAC
* módulo de folgas
* módulo de compensações
* efetivo
* viaturas
* dashboard operacional
* sistema de aprovações

Objetivo desta tarefa:

Implementar um novo módulo operacional chamado:

# "Férias"

O objetivo NÃO é criar um ERP completo de RH.

O objetivo é:

* permitir visualização operacional do efetivo indisponível
* auxiliar montagem de escalas
* visualizar policiais de férias/licença
* manter lógica semelhante ao módulo de folgas

---

## 2) Contexto operacional

Na PM:

* o policial possui:

  * férias
  * LP (Licença Prêmio)

Para o sistema:

* ambos seguirão a MESMA lógica operacional
* diferença apenas no tipo:

  * FERIAS
  * LP

Regras operacionais:

* períodos permitidos:

  * 15 dias
  * 30 dias
* qualquer outro período deve ser bloqueado

Exemplos válidos:

* 01/05 → 15/05
* 01/05 → 30/05

Exemplos inválidos:

* 10 dias
* 20 dias
* 5 dias

---

## 3) Regra de simultaneidade operacional

O sistema deve controlar sobreposição de períodos.

Regra:

* no máximo 2 policiais simultaneamente no mesmo dia
* considerar:

  * PENDING
  * REVIEW
  * APPROVED

Exemplo:

* Policial A:

  * 01/05 → 30/05

* Policial B:

  * 01/05 → 15/05

* Policial C:

  * 01/05 → 15/05

Resultado:

* Policial C deve entrar automaticamente em REVIEW

Outro exemplo:

* Policial A:

  * 01/05 → 30/05

* Policial B:

  * 01/05 → 15/05

* Policial C:

  * 16/05 → 30/05

Resultado:

* todos podem permanecer PENDING

IMPORTANTE:

A análise deve ser feita POR DIA e não apenas por mês.

---

## 4) Fluxo esperado

Fluxo:

1. policial acessa página "Férias"
2. visualiza calendário mensal
3. seleciona:

   * data inicial
   * data final
4. escolhe:

   * FERIAS
   * LP
5. sistema valida:

   * período permitido
   * conflitos operacionais
6. sistema cria solicitação:

   * PENDING
   * ou REVIEW automaticamente
7. ADMIN / N90 / TAT_CMD:

   * aprovam
   * rejeitam

Mesmo padrão operacional já existente nas folgas.

---

## 5) Regras importantes

NÃO implementar:

* controle de saldo
* controle de aquisição de benefício
* venda de LP
* regras complexas de RH

Objetivo é apenas:

* disponibilidade operacional
* visualização de efetivo indisponível
* apoio na montagem de escala

---

## 6) Reutilização de arquitetura existente

IMPORTANTE:

Reutilize ao máximo os padrões já existentes do módulo de folgas:

* services
* schemas
* approval flow
* logs
* statuses
* permissions
* calendar rendering
* UI patterns

Evite duplicação desnecessária de código.

Porém:

NÃO reutilize a tabela leave_requests diretamente.

Crie um módulo separado para manter arquitetura limpa.

Estrutura sugerida:

* vacation_requests
* vacation_approval_logs

---

## 7) Backend

Criar:

# Models

VacationRequest
VacationApprovalLog

Enums necessários:

VacationType:

* FERIAS
* LP

VacationStatus:

* PENDING
* REVIEW
* APPROVED
* REJECTED
* CANCELLED

Campos mínimos:

VacationRequest:

* id
* user_id
* vacation_type
* start_date
* end_date
* total_days
* status
* review_reason
* decision_reason
* approved_by
* approved_at
* created_at

VacationApprovalLog:

* id
* vacation_request_id
* actor_id
* action
* from_status
* to_status
* reason
* created_at

---

## 8) Regras backend

Implementar:

* cálculo de dias
* validação:

  * apenas 15 ou 30 dias
* validação de sobreposição operacional
* cálculo de simultaneidade por dia
* REVIEW automático quando exceder 2 simultâneos
* cancelamento
* approval/reject
* logs automáticos

IMPORTANTE:

A contagem deve considerar:

* PENDING
* REVIEW
* APPROVED

Ignorar:

* REJECTED
* CANCELLED

---

## 9) Rotas backend

Prefixo:

/vacations

Rotas mínimas:

GET:

* /vacations/calendar
* /vacations/pending

POST:

* /vacations/request

PATCH:

* /vacations/{id}/approve
* /vacations/{id}/reject
* /vacations/{id}/cancel

Permissões:

* solicitar:

  * qualquer usuário aprovado
* aprovar/rejeitar:

  * ADMIN
  * N90
  * TAT_CMD

---

## 10) Frontend

Adicionar nova opção na sidebar:

# "Férias"

Criar página:

/ferias

Visual:

* seguir identidade operacional atual
* dark theme
* mesma linguagem visual das folgas

---

## 11) Calendário operacional

O calendário deve:

* exibir períodos visivelmente
* permitir leitura rápida operacional
* destacar:

  * FERIAS
  * LP
  * PENDING
  * REVIEW
  * APPROVED

Objetivo:

Com o policial batendo o olho no calendário, ele deve entender rapidamente:

* quantos policiais estão afastados
* quais períodos possuem conflito
* quem estará indisponível para escala

---

## 12) UX esperada

Implementar:

* seleção de intervalo:

  * início
  * fim
* modal/form operacional
* feedback visual de conflito
* badges de status
* loading states
* tratamento de erros

---

## 13) Dashboard

Adicionar no dashboard operacional:

* resumo de férias pendentes
* resumo de períodos críticos
* quantidade de policiais afastados atualmente

Somente para:

* ADMIN
* N90
* TAT_CMD

---

## 14) Banco de dados

Criar:

* migrations Alembic
* enums PostgreSQL
* relacionamentos
* índices necessários

Seguir padrão já existente do projeto.

---

## 15) Estrutura esperada

Backend:

* models/vacation.py
* schemas/vacation.py
* services/vacation_service.py
* routes/vacations.py

Frontend:

* pages/FeriasPage.tsx
* services/vacationsApi.ts
* types/vacation.ts
* components/vacations/

---

## 16) Regras técnicas

IMPORTANTE:

* manter código limpo
* evitar overengineering
* evitar duplicação
* corrigir imports automaticamente
* manter consistência arquitetural do projeto atual
* manter tipagem forte no frontend
* manter responsividade mobile

---

## 17) Context7 MCP

Você DEVE obrigatoriamente utilizar Context7 MCP para consultar documentação atualizada antes de gerar código.

Consultar documentação recente de:

* FastAPI
* SQLAlchemy
* React
* TypeScript
* TailwindCSS

Se o Context7 MCP não estiver disponível:

Responder APENAS:

"Context7 MCP não disponível. Não posso continuar."

---

## 18) Formatação obrigatória da resposta

Responder EXATAMENTE nesta ordem:

1. Verificação do Context7
2. Docs consultados
3. Estratégia de implementação
4. Alterações backend
5. Alterações frontend
6. Estrutura de arquivos criada
7. Migrations necessárias
8. Variáveis de ambiente necessárias
9. Passo a passo dos comandos
10. Possíveis melhorias futuras

NÃO mostrar raciocínio interno.
Mostrar apenas resultado final.

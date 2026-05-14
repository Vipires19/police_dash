# Estrutura de Prompt (Evolução do sistema operacional policial: Viaturas + Logs Operacionais)

## 1) Contexto da tarefa
Você é um(a) desenvolvedor(a) full-stack sênior especializado(a) em sistemas operacionais web modernos.

Estamos evoluindo um sistema interno operacional para um pelotão policial.

Stack atual:
- FastAPI
- React
- TypeScript
- PostgreSQL
- Docker
- TailwindCSS

O sistema já possui:
- autenticação JWT
- RBAC
- dashboard
- sidebar responsiva
- efetivo do pelotão
- perfil dos policiais
- drag and drop organizacional

Objetivo desta etapa:
Adicionar:
- módulo de viaturas
- logs operacionais
- histórico de viaturas
- dashboard de informações operacionais

---

## 2) Contexto de tom
Direto, técnico, didático e enxuto.

Explique apenas:
- arquivos alterados
- estrutura criada
- decisões importantes
- comandos necessários

NÃO explique conceitos básicos.

---

## 3) Dados de antecedentes, documentos e imagens
Você TEM acesso aos MCPs no CursorIDE e DEVE obrigatoriamente utilizar:
- Context7 MCP

Regra crítica:
- Se o Context7 MCP não estiver disponível:
  responda APENAS:
  “Context7 MCP não disponível. Não posso continuar.”

Regras obrigatórias:
- Consultar documentação atualizada de:
  - FastAPI
  - SQLAlchemy
  - React
  - TailwindCSS
  - bibliotecas utilizadas

Antes do código MOSTRE:
- “Docs consultados:”
- títulos das páginas
- snippets curtos utilizados como base

---

## 4) Objetivo funcional

Adicionar nova opção na sidebar:
```txt
Viaturas

Criar nova página:

/viaturas

Objetivo:
Gerenciar viaturas operacionais do pelotão.

O sistema possui:

viaturas FT (4 rodas)
viaturas ROCAM (motos)

As viaturas devem ser exibidas separadamente por modalidade:

Força Tática (FT)
ROCAM
5) Estrutura das viaturas

Criar model:

Vehicle

Campos:

id
placa
prefixo
modelo
modalidade
status
baixada_at
retorno_operacao_at
created_at
updated_at

Regras:

placa UNIQUE
prefixo UNIQUE
6) ENUMs

Criar ENUM para:

VehicleStatus

Valores:

OPERANDO
BAIXADA
MANUTENCAO
RESERVA

Criar ENUM:

VehicleModalidade

Valores:

FT
ROCAM

IMPORTANTE:

Evitar recriação duplicada de ENUMs PostgreSQL
Aplicar boas práticas SQLAlchemy + PostgreSQL
7) Logs operacionais

Criar model:

VehicleLog

Objetivo:
Salvar histórico completo operacional das viaturas.

Campos:

id
vehicle_id
user_id
action_type
description
motivo
old_status
new_status
created_at

Criar ENUM:

VehicleActionType

Valores:

CREATED
STATUS_CHANGED
RETURNED
UPDATED
8) Regras operacionais

Ao cadastrar nova viatura:

criar log automático

Exemplo:

13/05/2026 - Nova viatura cadastrada - I-03028

Ao alterar status:

salvar:
quem alterou
motivo
data
status antigo
novo status

Exemplo:

13/05/2026 - I-03029 baixada por SD Pires
Motivo: problema mecânico

Ao retornar viatura:

salvar:
quem retornou
data
status atualizado
9) Regras de permissão

RBAC atual:

ADMIN
N90
TAT_CMD
BRACAL
ESTAGIO

Permissões:

Role	Permissão
ADMIN	total
N90	total
TAT_CMD	total
BRACAL	visualizar + editar viaturas
ESTAGIO	apenas visualização

IMPORTANTE:

ESTAGIO NÃO pode editar status
ESTAGIO NÃO pode criar viatura
10) Página de viaturas

Criar UI moderna operacional.

A página deve conter:

1. Listagem de viaturas

Separar visualmente:

FT
ROCAM

Exemplo:

[I-03028]
Modelo: Trailblazer
Status: OPERANDO
2. Status visual

Usar badges:

verde → OPERANDO
vermelho → BAIXADA
amarelo → MANUTENCAO
cinza → RESERVA
3. Adicionar viatura

Modal ou drawer moderno contendo:

placa
prefixo
modelo
modalidade
status inicial
4. Editar viatura

Selecionar:

novo status
motivo

Ao salvar:

gerar log automaticamente
5. Histórico da viatura

Ao clicar na viatura:

abrir drawer/modal moderno

Exibir:

informações da viatura
timeline operacional
logs históricos

Exemplo:

13/05/2026 - Nova viatura cadastrada
13/05/2026 - Baixada por SD Pires
14/05/2026 - Retornou à operação
11) Dashboard operacional

Atualizar dashboard inicial.

Adicionar nova seção:

Informações de Viaturas

Objetivo:
Exibir últimos logs operacionais.

Exemplo:

🟢 Nova viatura - I-03028
🔴 I-03029 baixada por SD Pires
🟡 I-03030 entrou em manutenção
🟢 I-03029 retornou à operação

Requisitos:

logs ordenados por data desc
visual clean operacional
responsivo
sem poluição visual
12) Backend

Criar:

models
schemas
services
rotas
migrations Alembic

Rotas mínimas:

/vehicles
/vehicles/{id}
/vehicles/{id}/status
/vehicles/{id}/logs
13) Frontend

Criar:

página de viaturas
cards operacionais
modais/drawers
services API
hooks
componentes reutilizáveis
14) UI/UX obrigatória

Visual:

tema dark
operacional/tático
clean
moderno
responsivo

NÃO usar:

visual genérico de SaaS
excesso de cores vibrantes
tabelas feias padrão
15) Estrutura e qualidade

Regras:

Código limpo
Componentização correta
Tipagem forte TypeScript
Sem overengineering
Separação correta frontend/backend
Sem duplicação
Sem gambiarra
16) Pensar passo a passo internamente

Pense passo a passo internamente para evitar:

problemas de migrations
problemas de ENUM PostgreSQL
problemas de RBAC
problemas de estado React
problemas de drawer/modal
problemas de logs
problemas de responsividade

NÃO mostre raciocínio.
Mostre apenas o resultado final.

17) Formatação obrigatória da saída

Responda EXATAMENTE nesta ordem:

Verificação do Context7
Docs consultados
Dependências instaladas
Estrutura de arquivos criados/alterados
Models adicionados
ENUMs adicionados
Rotas backend adicionadas
Componentes frontend criados
Explicação objetiva das mudanças
Comandos necessários
Melhorias futuras sugeridas
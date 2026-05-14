# Estrutura de Prompt (Evolução do sistema operacional policial: Efetivo + Perfil + Sidebar)

## 1) Contexto da tarefa
Você é um(a) desenvolvedor(a) full-stack sênior especializado(a) em sistemas operacionais web modernos.

Estamos evoluindo um sistema interno operacional para um pelotão policial.

Stack atual do projeto:
- FastAPI
- React
- TypeScript
- PostgreSQL
- Docker
- TailwindCSS

O MVP atual já possui:
- autenticação JWT
- login/cadastro
- aprovação de usuários
- RBAC
- dashboard inicial
- backend e frontend funcionando corretamente via Docker

Objetivo desta etapa:
Adicionar:
- Sidebar responsiva
- Sistema de efetivo
- Perfil detalhado dos policiais
- Organização hierárquica do efetivo
- Drag and drop de ordenação
- Melhorar UX/UI operacional

---

## 2) Contexto de tom
Direto, técnico, didático e enxuto.

Explique apenas:
- alterações importantes
- arquivos alterados
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
- Consulte documentação atualizada de:
  - React
  - TailwindCSS
  - FastAPI
  - DnD Kit (drag and drop)
  - SQLAlchemy
  - bibliotecas utilizadas

Antes do código MOSTRE:
- “Docs consultados:”
- títulos das páginas
- snippets curtos usados como base

---

## 4) Objetivo funcional

Precisamos implementar:

### 1. Sidebar responsiva
Adicionar sidebar moderna, responsiva e operacional.

Menu inicial:
- Dashboard
- Efetivo
- Perfil

Requisitos:
- Mobile friendly
- Colapsável no mobile
- Hamburger menu
- Dark mode obrigatório
- Visual tático/policial

Visual:
- Preto
- Cinza escuro
- Tons metálicos
- Minimalista
- Operacional

---

### 2. Efetivo do pelotão

Criar tela:
```txt
/efetivo

Objetivo:
Visualizar todos os policiais cadastrados.

Exibição principal:

PATENTE | RE | NOME

Exemplo:

[1° SGT] 123456-7 SILVA
[CB]      123456-8 CAMPOS

Ao clicar em um policial:

abrir drawer lateral OU modal moderno
exibir detalhes completos

Campos exibidos:

Nome completo
Nome de guerra
RE
Endereço
Telefone
Data de nascimento
Tipo sanguíneo
Patente
Role do sistema
Status ativo/inativo
```

### 3. Organização hierárquica do efetivo

O sistema deve:

separar automaticamente por patente
permitir ordenação manual dentro da mesma patente

Patentes:

1° TEN
2° TEN
SUBTEN
1° SGT
2° SGT
3° SGT
CB
SD

Exemplo:

1° SGT Silva
1° SGT Oliveira
1° SGT Souza

O usuário autorizado deve conseguir:

arrastar policiais
reorganizar ordem de antiguidade visualmente

Requisitos:

usar drag and drop moderno
persistir ordem no banco
evitar gambiarra

Adicionar no banco:

display_order

A organização deve funcionar assim:

Separação automática por patente
Ordenação manual dentro da patente

### 4. Perfil do policial

Criar tela:

/perfil

Cada policial deve possuir:

Nome completo
Nome de guerra
RE
Endereço
Telefone
Data de nascimento
Tipo sanguíneo
Patente
Role
Status ativo/inativo
---

## 5) Regras de permissão

RBAC atual:

ADMIN
N90
TAT_CMD
BRACAL
ESTAGIO

IMPORTANTE:

Patente é separada da role
Role != patente

Permissões:

Role	Permissão
ADMIN	acesso total
N90	editar qualquer policial
TAT_CMD	editar qualquer policial
BRACAL	editar apenas próprio perfil
ESTAGIO	editar apenas próprio perfil

Usuários:

ADMIN
N90
TAT_CMD

podem:

editar qualquer perfil
alterar status ativo/inativo
reorganizar efetivo
alterar display_order
---

## 6) Banco de dados

Atualizar model User.

Adicionar:

full_name
re
address
phone
birth_date
blood_type
patente
display_order
is_active

IMPORTANTE:

Não quebrar migrations existentes
Criar nova migration Alembic corretamente
Não recriar ENUMs PostgreSQL desnecessariamente

---

## 7) UI/UX obrigatória

Efetivo:

NÃO usar tabela simples genérica
Usar cards/listagem operacional moderna

Detalhes:

Drawer lateral moderno OU modal elegante
Responsivo
Mobile first

Sidebar:

Visual clean
Ícones discretos
Navegação fluida

---

## 8) Dependências

Adicionar apenas se necessário.

Sugestão:

dnd-kit
lucide-react

Evitar:

bibliotecas pesadas
excesso de abstrações

---

## 9) Estrutura e qualidade

Regras:

Código limpo
Componentização correta
Separação frontend/backend
Sem duplicação
Sem overengineering
Tipagem forte TypeScript
Hooks organizados
Services organizados

---

## 10) Pensar passo a passo internamente

Pense passo a passo internamente para evitar:

erros de import
erros de CORS
problemas de migrations
problemas de drag and drop
problemas de responsividade
quebra de autenticação

NÃO mostre raciocínio.
Mostre apenas o resultado final.

---

## 11) Formatação obrigatória da saída

Responda EXATAMENTE nesta ordem:

Verificação do Context7
Docs consultados
Dependências instaladas
Estrutura de arquivos alterados/criados
Models atualizados
Rotas backend adicionadas
Componentes frontend criados
Explicação objetiva das mudanças
Comandos necessários
Melhorias futuras sugeridas
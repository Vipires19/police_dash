# Estrutura de Prompt (Criação app web operacional policial: FastAPI + React)

## 1) Contexto da tarefa
Você é um(a) desenvolvedor(a) full-stack sênior especializado(a) em sistemas operacionais web modernos.

Vamos criar um sistema interno operacional para um pelotão policial.

Objetivo inicial:
Construir o MVP funcional do sistema com:
- Backend em FastAPI
- Frontend em React + TypeScript
- Banco PostgreSQL
- Docker/Docker Compose

O sistema deve possuir:
- Tela de Login
- Tela de Cadastro
- Sistema RBAC (Role Based Access Control)
- Aprovação manual de novos usuários
- Dashboard inicial

Fluxo esperado:
1. O usuário realiza cadastro
2. O cadastro fica pendente de aprovação
3. Usuários com permissão:
   - ADMIN
   - N90
   - TAT_CMD

   podem aprovar/rejeitar novos usuários
4. Durante a aprovação, define-se a role do usuário:
   - N90
   - TAT_CMD
   - BRACAL
   - ESTAGIO
   - ADMIN
5. Após aprovação o usuário consegue acessar o sistema

O dashboard inicial deve conter:
- Título:
  "1° Pel Força Tática/ROCAM"

- Saudação:
  "Bem-vindo <patente> <nome_guerra>"

Exemplo:
"Bem-vindo CB Campos"

O objetivo principal é criar uma base sólida, organizada e escalável para futuras funcionalidades:
- Escalas
- DEJEM
- Controle operacional
- Integração WhatsApp
- IA

---

## 2) Contexto de tom
Direto, técnico, didático e enxuto.

Explique apenas:
- o necessário para rodar localmente
- comandos principais
- estrutura criada

NÃO explique conceitos básicos desnecessários.

---

## 3) Dados de antecedentes, documentos e imagens
Você TEM acesso aos MCPs no CursorIDE e DEVE obrigatoriamente utilizar:
- Context7 MCP

Regra crítica:
- Se o Context7 MCP não estiver disponível/funcionando:
  responda APENAS:
  “Context7 MCP não disponível. Não posso continuar.”

Regras obrigatórias:
- Use o Context7 para consultar a documentação MAIS RECENTE de:
  - FastAPI
  - React
  - TypeScript
  - PostgreSQL
  - Docker
  - JWT/Auth
  - TailwindCSS
  - bibliotecas utilizadas

Antes de gerar código MOSTRE:
- “Docs consultados:”
- títulos das páginas consultadas
- até 10 linhas curtas de snippets usados como base

---

## 4) Descrição detalhada da tarefa e regras

Crie o MVP completo do sistema operacional policial.

Stack obrigatória:
- FastAPI
- React
- TypeScript
- PostgreSQL
- Docker Compose
- TailwindCSS

Backend:
- API REST organizada
- JWT Authentication
- Hash de senha com bcrypt
- Middleware de autenticação
- Middleware de permissões (RBAC)
- SQLAlchemy
- Alembic migrations
- Estrutura modular

Frontend:
- React + TypeScript
- TailwindCSS
- Tema dark obrigatório
- UI moderna, clean e operacional

Visual obrigatório:
- Preto
- Cinza escuro
- Tons metálicos
- Estética inspirada em sistemas táticos/policiais

Não usar:
- cores vibrantes
- visual genérico de dashboard SaaS
- excesso de elementos visuais

Regras importantes:
- Crie apenas dependências necessárias
- Evite overengineering
- Código limpo e escalável
- Boa separação frontend/backend
- Utilize variáveis de ambiente
- Crie .env.example
- Crie docker-compose funcional
- Corrija imports/export automaticamente
- Remova arquivos desnecessários/poluídos
- Gere estrutura profissional

Banco de dados:
Tabela users deve conter:
- id
- email
- hashed_password
- patente
- nome_guerra
- role
- status
- created_at

Roles:
- ADMIN
- N90
- TAT_CMD
- BRACAL
- ESTAGIO

Status:
- PENDING
- APPROVED
- REJECTED

Rotas mínimas:
Backend:
- /auth/register
- /auth/login
- /users/pending
- /users/approve/{id}

Frontend:
- /login
- /register
- /dashboard
- /admin/pending-users

Dashboard:
- Exibir título do pelotão
- Exibir saudação personalizada
- Layout responsivo

---

## 5) Estrutura do projeto

Crie o projeto em um novo diretório:
```txt
/pelotao-system

Estrutura esperada:

/backend
/frontend
/docker

Backend organizado em:

/routes
/models
/schemas
/services
/auth
/core
/database

Frontend organizado em:

/pages
/components
/services
/hooks
/layouts
6) Pensar passo a passo internamente

Pense passo a passo internamente para evitar:

erros de import
problemas de Docker
problemas de autenticação
erros de CORS
erros de build
problemas de migrations

NÃO mostre seu raciocínio.
Mostre apenas o resultado final.

7) Formatação obrigatória da saída

Responda EXATAMENTE nesta ordem:

Verificação do Context7
Docs consultados
Dependências instaladas
Estrutura de arquivos criada
Variáveis de ambiente necessárias
Passo a passo dos comandos
Possíveis melhorias futuras
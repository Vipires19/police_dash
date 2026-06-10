# Implementação do módulo Operacional - Veículos C05

## Contexto

Estamos implementando um novo módulo operacional para monitoramento de veículos relacionados a ações criminosas, denúncias, atitudes suspeitas e demais ocorrências de interesse policial.

Este módulo é independente do módulo já existente:

Operacional → Veículos Produtos de Crime

Não reutilizar tabelas do módulo de Furto/Roubo.

Criar estrutura própria.

---

## Objetivo operacional

Permitir:

* Cadastro de veículos monitorados
* Registro histórico de informações
* Consulta rápida
* Impressão de folha operacional
* Acompanhamento contínuo de veículos de interesse

Exemplos:

* Veículo visto em ponto de tráfico
* Veículo denunciado
* Veículo frequentemente abordado
* Veículo associado a atitude suspeita
* Veículo relacionado a ocorrências específicas

---

# Estrutura do Menu

Adicionar novo item:

Operacional
└── Veículos C05

Não alterar ainda a estrutura da sidebar.

A reorganização será feita em etapa posterior.

---

# Cadastro

Campos:

Placa

Modelo

Cor

Ano

QRU

Anotação Inicial

---

## QRU

O QRU NÃO deve ser texto livre.

Criar tabela própria para códigos operacionais.

Exemplo:

F01
F02
F03

Cada código possuirá descrição própria.

O cadastro do veículo deve utilizar dropdown.

Exemplo:

F01 - Drogas

F02 - Roubo

F03 - Receptação

---

# Banco de Dados

Criar tabela:

criminal_watch_vehicles

Campos:

id

plate

vehicle_model

color

year

qru_code_id

created_at

created_by_id

---

Criar tabela:

criminal_watch_notes

Campos:

id

vehicle_id

note

created_at

created_by_id

---

Criar tabela:

vehicle_qru_codes

Campos:

id

code

description

is_active

created_at

created_by_id

---

# Cadastro inicial

Ao cadastrar um veículo:

Criar registro em:

criminal_watch_vehicles

e

criminal_watch_notes

utilizando a anotação inicial.

---

# Pesquisa

Criar tela de pesquisa.

Permitir busca por:

* placa
* modelo
* cor
* QRU

---

# Resultado da pesquisa

Exibir:

Placa

Modelo

Cor

Ano

QRU

Data de cadastro

---

# Ficha Técnica

Ao clicar em um veículo:

Abrir página/modal contendo:

Placa

Modelo

Cor

Ano

QRU

Descrição do QRU

Data de cadastro

Usuário que cadastrou

---

# Histórico Operacional

Exibir histórico completo de anotações.

Exemplo:

08/06/2026
Visto em ponto de tráfico.

09/06/2026
Abordado pela FT.

12/06/2026
Denúncia anônima recebida.

---

# Nova anotação

Permitir adicionar novas observações.

Campo:

Nova anotação

Botão:

Adicionar

A anotação deve ser salva em:

criminal_watch_notes

Sem sobrescrever registros anteriores.

---

# Exclusão

Permitir exclusão do veículo.

Motivo:

* cadastro duplicado
* erro de digitação
* registro incorreto

Remover:

* veículo
* anotações vinculadas

---

# Impressão Operacional

Criar página de impressão semelhante à folha física utilizada pela equipe.

HTML + CSS

Sem PDF nesta fase.

---

# Layout da folha

Exibir os 15 registros mais recentes.

Preenchimento:

de baixo para cima

igual à lógica já utilizada na folha 0 a 9.

---

# Campos impressos

Exemplo:

ABC1D23

Deve ser exibido como:

1D23 | ABC | COROLLA | PTO | 22 | F01

Colunas:

1. Parte numérica da placa
2. Letras da placa
3. Modelo
4. Cor
5. Ano
6. QRU

---

# Histórico

A folha deve exibir apenas:

15 registros mais recentes

Porém:

Todos os registros devem permanecer armazenados no banco.

Quando entrar o 16º:

* sai da folha
* continua pesquisável
* continua no histórico

---

# CRUD de QRUs

Criar tela administrativa simples.

Permitir:

Listar

Cadastrar

Editar

Desativar

---

# Backend

Criar:

Models

Schemas

Services

Routes

Seguindo o padrão atual do projeto.

---

# Frontend

Criar:

Pages

Components

Types

Services

Seguindo o padrão já utilizado em:

Veículos Produtos de Crime

---

# Restrições

Não alterar:

* Escalas
* Viaturas
* Efetivo
* Folgas
* Compensações
* Veículos Produtos de Crime

Implementar apenas o novo módulo.

---

# Antes de iniciar

Mostrar:

1. Arquivos que serão criados
2. Migration planejada
3. Estrutura das tabelas
4. Fluxo da funcionalidade

Somente depois iniciar a implementação.

---

# Após concluir

Mostrar:

* migrations criadas
* endpoints criados
* componentes criados
* arquivos modificados
* resumo da implementação

Introdução

O módulo DEJEM foi modelado utilizando princípios de Domain Driven Design.

O objetivo é representar o processo real de distribuição das vagas através de entidades de negócio independentes.

O módulo possui um único Aggregate Root:

Campaign

Todos os demais objetos pertencem a uma campanha.

Aggregate Root
Campaign

Representa uma campanha mensal.

Responsabilidades
controlar o ciclo de vida da campanha
controlar oferta
controlar interesses
controlar distribuição
impedir alterações quando encerrada
Estados
OPEN

↓

DISTRIBUTED

↓

RUNNING

↓

CLOSED
Entidade
OfferEvent

Representa qualquer alteração na quantidade de vagas.

Exemplos.

+100

+10

-3

Campos.

id

campaign_id

type

quantity

reason

created_at

created_by

Nunca é alterado.

Entidade
Interest

Representa a manifestação de interesse do policial.

Campos.

id

campaign_id

police_id

desired_slots

status

created_at

updated_at

Status.

ACTIVE

CANCELLED
Entidade
Allocation

Representa o resultado produzido pelo algoritmo.

Campos.

campaign_id

police_id

allocated_slots

algorithm_version

created_at

Uma Allocation nunca representa uma escala.

Ela apenas informa quantos créditos foram atribuídos.

Entidade
Credit

Representa uma vaga individual.

Cada crédito possui identidade própria.

Campos.

id

campaign

allocation

status

schedule_id

created_at

Status.

AVAILABLE

SCHEDULED

EXECUTED

CANCELLED

TRANSFERRED
Entidade
Schedule

Pertence ao módulo de Escalas.

O Allocation Engine apenas consome ou libera créditos.
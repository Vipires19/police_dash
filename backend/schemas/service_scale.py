from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from models.service_scale import ScaleLogAction, ScaleModality, ScaleStatus
from models.user import OrganizationalUnit
from schemas.dejem import DejemMapBlock

FT_MISSION_PRESETS = ("Tático Comando", "Supervisor Tático", "Força Tática")
ROCAM_MISSION_PRESETS = ("ROCAM 1", "ROCAM 2", "ROCAM 3")

MAX_FT_MEMBERS = 4
MAX_ROCAM_MEMBERS = 3


class ScaleTeamMemberInput(BaseModel):
    user_id: int
    assigned_vehicle_id: int | None = None
    role_label: str | None = Field(default=None, max_length=64)


class ScaleTeamMemberPublic(BaseModel):
    id: int
    user_id: int
    patente: str
    nome_guerra: str
    display_order: int
    assigned_vehicle_id: int | None
    assigned_vehicle_prefixo: str | None
    role_label: str | None

    model_config = {"from_attributes": False}


class ScaleTeamPublic(BaseModel):
    id: int
    modality: ScaleModality
    vehicle_id: int | None
    vehicle_prefixo: str | None
    vehicle_placa: str | None
    start_datetime: datetime
    end_datetime: datetime
    mission_name: str
    notes: str | None
    members: list[ScaleTeamMemberPublic]

    model_config = {"from_attributes": False}


class ServiceScaleCreate(BaseModel):
    scale_date: date
    title: str = Field(..., min_length=1, max_length=256)
    description: str | None = Field(default=None, max_length=4000)
    fardamento: str | None = Field(default=None, max_length=256)
    status: ScaleStatus = ScaleStatus.DRAFT


class ServiceScaleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=256)
    description: str | None = Field(default=None, max_length=4000)
    fardamento: str | None = Field(default=None, max_length=256)


class ScaleTeamCreate(BaseModel):
    modality: ScaleModality
    vehicle_id: int | None = None
    start_datetime: datetime
    end_datetime: datetime
    mission_name: str = Field(..., min_length=1, max_length=256)
    notes: str | None = Field(default=None, max_length=4000)
    members: list[ScaleTeamMemberInput] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_range(self) -> "ScaleTeamCreate":
        if self.end_datetime <= self.start_datetime:
            raise ValueError("Horário final deve ser posterior ao inicial")
        if self.modality == ScaleModality.ROCAM:
            if self.vehicle_id is not None:
                raise ValueError("Equipe ROCAM não possui viatura principal")
            for m in self.members:
                if not m.assigned_vehicle_id:
                    raise ValueError("Cada policial ROCAM deve ter uma moto vinculada")
        elif self.modality == ScaleModality.FT and not self.vehicle_id:
            raise ValueError("Viatura FT é obrigatória")
        return self


class ScaleTeamUpdate(BaseModel):
    modality: ScaleModality | None = None
    vehicle_id: int | None = None
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    mission_name: str | None = Field(default=None, min_length=1, max_length=256)
    notes: str | None = Field(default=None, max_length=4000)
    members: list[ScaleTeamMemberInput] | None = None

    @model_validator(mode="after")
    def validate_modality_rules(self) -> "ScaleTeamUpdate":
        if self.members is None:
            return self
        if self.modality == ScaleModality.ROCAM:
            for m in self.members:
                if not m.assigned_vehicle_id:
                    raise ValueError("Cada policial ROCAM deve ter uma moto vinculada")
        return self


class ScaleTeamMembersUpdate(BaseModel):
    members: list[ScaleTeamMemberInput]

    @model_validator(mode="after")
    def validate_members(self) -> "ScaleTeamMembersUpdate":
        if not self.members:
            raise ValueError("Informe ao menos um policial")
        return self


class ServiceScalePublic(BaseModel):
    id: int
    scale_date: date
    title: str
    description: str | None
    fardamento: str | None = None
    status: ScaleStatus
    created_by_id: int
    created_by_label: str | None = None
    published_at: datetime | None
    current_version_number: int | None = None
    created_at: datetime
    updated_at: datetime
    teams: list[ScaleTeamPublic]

    model_config = {"from_attributes": False}


class ScaleVersionPublic(BaseModel):
    id: int
    service_scale_id: int
    version_number: int
    published_at: datetime
    published_by_id: int
    published_by_label: str | None = None
    change_summary: str | None = None
    dejem_integrated_count: int = 0
    created_at: datetime


class ScaleVersionDetail(ScaleVersionPublic):
    export_text: str


class ScaleCalendarDay(BaseModel):
    date: date
    scale_id: int | None
    title: str | None
    status: ScaleStatus | None
    team_count: int


class ScaleCalendarResponse(BaseModel):
    year: int
    month: int
    days: list[ScaleCalendarDay]


class StaffAbsenceFlag(BaseModel):
    kind: str
    label: str


class StaffRosterEntry(BaseModel):
    user_id: int
    patente: str
    nome_guerra: str
    display_order: int
    operational_rank: int
    organizational_unit: OrganizationalUnit
    absences: list[StaffAbsenceFlag]


class ScaleVehicleOption(BaseModel):
    id: int
    prefixo: str
    placa: str
    modalidade: str


class ScaleDayDetailResponse(BaseModel):
    scale: ServiceScalePublic | None
    staff_roster: list[StaffRosterEntry]
    vehicles_ft: list[ScaleVehicleOption]
    vehicles_ro_cam: list[ScaleVehicleOption]
    dejem_blocks: list[DejemMapBlock] = Field(default_factory=list)


class ScaleLogFeedItem(BaseModel):
    id: int
    service_scale_id: int
    scale_date: date
    scale_title: str
    action_type: ScaleLogAction
    description: str
    created_at: datetime
    actor_label: str

    model_config = {"from_attributes": False}


class ScaleHistoryEntry(BaseModel):
    id: int
    scale_date: date
    title: str
    status: ScaleStatus
    team_count: int
    published_at: datetime | None
    updated_at: datetime

    model_config = {"from_attributes": False}


class ScaleHistoryResponse(BaseModel):
    items: list[ScaleHistoryEntry]
    total: int


class ScaleExportResponse(BaseModel):
    text: str


class ScalePublishPreviewRequest(BaseModel):
    description: str | None = Field(default=None, max_length=4000)


class ScalePublishPreviewResponse(BaseModel):
    text: str
    fardamento: str | None = None
    description: str | None = None
    team_count: int = 0
    dejem_count: int = 0


class ScaleMessageTemplatePublic(BaseModel):
    id: int
    slug: str
    name: str
    body_text: str
    is_default: bool
    is_active: bool

    model_config = {"from_attributes": True}

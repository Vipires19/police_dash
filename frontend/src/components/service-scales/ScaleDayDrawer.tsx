import { useEffect, useMemo, useState } from "react";
import { Pencil, Share2, Trash2, X } from "lucide-react";
import { ScaleExportModal } from "./ScaleExportModal";
import { ScalePublishPreviewModal } from "./ScalePublishPreviewModal";
import { ScaleVersionsPanel } from "./ScaleVersionsPanel";
import {
  sortMembersByRole,
  teamRolesFor,
  type ScaleDayDetailResponse,
  type ScaleModality,
  type ScaleTeamMemberInput,
  type ScaleTeamPublic,
  type StaffRosterEntry,
} from "@/types/serviceScale";
import {
  ORGANIZATIONAL_UNIT_ORDER,
  ORGANIZATIONAL_UNIT_SECTION_LABELS,
  type OrganizationalUnit,
} from "@/types";
import { useAuth } from "@/hooks/AuthContext";
import { absenceBadgeClass, absenceDisplayLabel, scaleStatusBadgeClass, scaleStatusLabel } from "./statusStyles";
import {
  filterFtVehicles,
  filterRoCamMotos,
  gatherScaleUsage,
  isUserAvailable,
} from "./scaleAvailability";
import {
  assignedUserIds,
  emptyRoleAssignments,
  membersToRoleAssignments,
  membersToRoleBikes,
  setRoleUser,
  type RoleAssignments,
  type RoleBikes,
} from "./teamRoles";
import { MissionPresetSelect, missionToPreset, resolveMissionName } from "./missionPresets";

type PlatoonFilter = "ALL" | OrganizationalUnit;

const COMPANY_FILTER_ROLES = new Set(["ADMIN", "CMD_TATICO"]);

function defaultPlatoonFilter(role: string | undefined, unit: OrganizationalUnit | undefined): PlatoonFilter {
  if (role && COMPANY_FILTER_ROLES.has(role)) return "ALL";
  return unit ?? "ALL";
}

function canChangePlatoonFilter(role: string | undefined): boolean {
  return Boolean(role && COMPANY_FILTER_ROLES.has(role));
}

function classifyAbsenceKey(kind: string, label?: string): "FOLGA" | "DS" | "FERIAS" | "LP" | "LICENCA" | "OUTROS" {
  const display = absenceDisplayLabel(kind, label);
  if (display === "DS") return "DS";
  if (display === "FÉRIAS") return "FERIAS";
  if (display === "LP") return "LP";
  if (display === "LICENÇA") return "LICENCA";
  if (display === "FOLGA") return "FOLGA";
  return "OUTROS";
}

function buildRosterSummary(roster: StaffRosterEntry[], usage: ReturnType<typeof gatherScaleUsage>) {
  let disponiveis = 0;
  let emServico = 0;
  let folga = 0;
  let ds = 0;
  let ferias = 0;
  let lp = 0;
  let licenca = 0;
  let outros = 0;

  for (const s of roster) {
    if (s.absences.length === 0) {
      disponiveis += 1;
      if (!isUserAvailable(s.user_id, usage)) emServico += 1;
      continue;
    }
    const keys = new Set(s.absences.map((a) => classifyAbsenceKey(a.kind, a.label)));
    if (keys.has("DS")) ds += 1;
    else if (keys.has("FOLGA")) folga += 1;
    if (keys.has("FERIAS")) ferias += 1;
    if (keys.has("LP")) lp += 1;
    if (keys.has("LICENCA")) licenca += 1;
    if (keys.has("OUTROS")) outros += 1;
  }

  return { disponiveis, emServico, folga, ds, ferias, lp, licenca, outros };
}

function formatDt(iso: string): string {
  return new Date(iso).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function toLocalInput(iso: string): string {
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function toLocalInputFromDate(isoDate: string, hour: number): string {
  const d = new Date(isoDate + "T12:00:00");
  d.setHours(hour, 0, 0, 0);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

type TeamFormPayload = {
  modality: ScaleModality;
  vehicle_id: number | null;
  start_datetime: string;
  end_datetime: string;
  mission_name: string;
  notes: string | null;
  members: ScaleTeamMemberInput[];
};

interface Props {
  open: boolean;
  isoDate: string;
  detail: ScaleDayDetailResponse | null;
  canEdit: boolean;
  busy: boolean;
  onClose: () => void;
  onCreateScale: (title: string) => void;
  onUpdateScale?: (
    scaleId: number,
    body: { fardamento?: string | null; description?: string | null },
  ) => void | Promise<void>;
  onPublish: (scaleId: number) => void;
  onUnpublish: (scaleId: number) => void;
  onAddTeam: (scaleId: number, payload: TeamFormPayload) => void;
  onEditTeam: (teamId: number, payload: TeamFormPayload) => void;
  onRemoveTeam: (teamId: number) => void;
  onDeleteScale: (scaleId: number) => void;
}

export function ScaleDayDrawer({
  open,
  isoDate,
  detail,
  canEdit,
  busy,
  onClose,
  onCreateScale,
  onUpdateScale,
  onPublish,
  onUnpublish,
  onAddTeam,
  onEditTeam,
  onRemoveTeam,
  onDeleteScale,
}: Props) {
  const { user } = useAuth();
  const scale = detail?.scale ?? null;
  const dejemBlocks = detail?.dejem_blocks ?? [];
  const [title, setTitle] = useState("");
  const [fardamentoDraft, setFardamentoDraft] = useState("");
  const [obsDraft, setObsDraft] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editingTeam, setEditingTeam] = useState<ScaleTeamPublic | null>(null);
  const [modality, setModality] = useState<ScaleModality>("FT");
  const [vehicleId, setVehicleId] = useState<number | "">("");
  const [missionPreset, setMissionPreset] = useState("");
  const [missionCustom, setMissionCustom] = useState("");
  const [notes, setNotes] = useState("");
  const [startAt, setStartAt] = useState(() => toLocalInputFromDate(isoDate, 6));
  const [endAt, setEndAt] = useState(() => toLocalInputFromDate(isoDate, 18));
  const [roleAssignments, setRoleAssignments] = useState<RoleAssignments>(() => emptyRoleAssignments("FT"));
  const [roleBikes, setRoleBikes] = useState<RoleBikes>({});
  const [exportOpen, setExportOpen] = useState(false);
  const [publishPreviewOpen, setPublishPreviewOpen] = useState(false);
  const [platoonFilter, setPlatoonFilter] = useState<PlatoonFilter>(() =>
    defaultPlatoonFilter(user?.role, user?.organizational_unit),
  );

  const platoonFilterLocked = !canChangePlatoonFilter(user?.role);

  useEffect(() => {
    if (!open) return;
    setPlatoonFilter(defaultPlatoonFilter(user?.role, user?.organizational_unit));
  }, [open, user?.role, user?.organizational_unit]);

  const displayDate = useMemo(
    () =>
      new Date(isoDate + "T12:00:00").toLocaleDateString("pt-BR", {
        weekday: "long",
        day: "2-digit",
        month: "long",
        year: "numeric",
      }),
    [isoDate],
  );

  const usage = useMemo(
    () => gatherScaleUsage(scale?.teams ?? [], editingTeam?.id),
    [scale?.teams, editingTeam?.id],
  );

  const ftVehicles = useMemo(
    () => filterFtVehicles(detail?.vehicles_ft ?? [], usage, editingTeam?.vehicle_id),
    [detail?.vehicles_ft, usage, editingTeam?.vehicle_id],
  );

  const roCamMotos = useMemo(() => detail?.vehicles_ro_cam ?? [], [detail?.vehicles_ro_cam]);

  const selectedMembers = useMemo(() => assignedUserIds(roleAssignments), [roleAssignments]);
  const teamRoleList = useMemo(() => teamRolesFor(modality), [modality]);

  const { availableRoster, awayRoster } = useMemo(() => {
    const roster = detail?.staff_roster ?? [];
    // Já selecionados (ex.: edição) permanecem no grupo disponível para visualização.
    const available = roster.filter(
      (s) => s.absences.length === 0 || selectedMembers.includes(s.user_id),
    );
    const away = roster.filter(
      (s) => s.absences.length > 0 && !selectedMembers.includes(s.user_id),
    );
    return { availableRoster: available, awayRoster: away };
  }, [detail?.staff_roster, selectedMembers]);

  const filteredAvailableRoster = useMemo(() => {
    if (platoonFilter === "ALL") return availableRoster;
    return availableRoster.filter((s) => s.organizational_unit === platoonFilter);
  }, [availableRoster, platoonFilter]);

  const rosterSummary = useMemo(
    () => buildRosterSummary(detail?.staff_roster ?? [], usage),
    [detail?.staff_roster, usage],
  );

  const missionName = resolveMissionName(missionPreset, missionCustom);
  const isEdit = editingTeam !== null;

  const resetForm = () => {
    setEditingTeam(null);
    setFormOpen(false);
    setModality("FT");
    setVehicleId("");
    setMissionPreset("");
    setMissionCustom("");
    setNotes("");
    setStartAt(toLocalInputFromDate(isoDate, 6));
    setEndAt(toLocalInputFromDate(isoDate, 18));
    setRoleAssignments(emptyRoleAssignments("FT"));
    setRoleBikes({});
  };

  const openAddForm = () => {
    resetForm();
    setFormOpen(true);
  };

  const openEditForm = (team: ScaleTeamPublic) => {
    const { preset, custom } = missionToPreset(team.mission_name, team.modality);
    setEditingTeam(team);
    setFormOpen(true);
    setModality(team.modality);
    setVehicleId(team.vehicle_id ?? "");
    setMissionPreset(preset);
    setMissionCustom(custom);
    setNotes(team.notes ?? "");
    setStartAt(toLocalInput(team.start_datetime));
    setEndAt(toLocalInput(team.end_datetime));
    setRoleAssignments(membersToRoleAssignments(team));
    setRoleBikes(membersToRoleBikes(team));
  };

  useEffect(() => {
    if (!open) resetForm();
  }, [open, isoDate]);

  useEffect(() => {
    setFardamentoDraft(scale?.fardamento ?? "");
    setObsDraft(scale?.description ?? "");
  }, [scale?.id, scale?.fardamento, scale?.description]);

  const buildPayload = (): TeamFormPayload | null => {
    if (!missionName || selectedMembers.length === 0) return null;
    if (modality === "FT" && vehicleId === "") return null;
    if (modality === "ROCAM") {
      for (const role of teamRoleList) {
        const uid = roleAssignments[role];
        if (typeof uid === "number" && !roleBikes[role]) return null;
      }
    }

    const members: ScaleTeamMemberInput[] = teamRoleList
      .filter((role) => typeof roleAssignments[role] === "number")
      .map((role) => ({
        user_id: roleAssignments[role] as number,
        role_label: role,
        assigned_vehicle_id:
          modality === "ROCAM" ? (roleBikes[role] as number) : null,
      }));

    if (members.length === 0) return null;

    return {
      modality,
      vehicle_id: modality === "FT" ? Number(vehicleId) : null,
      start_datetime: new Date(startAt).toISOString(),
      end_datetime: new Date(endAt).toISOString(),
      mission_name: missionName,
      notes: notes.trim() || null,
      members,
    };
  };

  const submitForm = () => {
    const payload = buildPayload();
    if (!scale || !payload) return;
    if (isEdit && editingTeam) onEditTeam(editingTeam.id, payload);
    else onAddTeam(scale.id, payload);
    resetForm();
  };

  if (!open) return null;

  return (
    <aside className="fixed inset-y-0 right-0 z-50 flex w-full max-w-lg flex-col border-l border-zinc-800 bg-zinc-950 shadow-2xl">
      <header className="flex items-start justify-between gap-3 border-b border-zinc-800 px-5 py-4">
        <div>
          <p className="text-[10px] uppercase tracking-wider text-zinc-500">Escala do dia</p>
          <h2 className="mt-1 text-lg font-semibold capitalize text-zinc-50">{displayDate}</h2>
          {scale && (
            <span
              className={`mt-2 inline-block rounded px-2 py-0.5 text-[10px] font-semibold uppercase ring-1 ${scaleStatusBadgeClass(scale.status)}`}
            >
              {scaleStatusLabel(scale.status)}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded p-2 text-zinc-400 hover:bg-zinc-900 hover:text-white"
          aria-label="Fechar"
        >
          <X className="h-5 w-5" />
        </button>
      </header>

      <div className="flex-1 overflow-y-auto px-5 py-4">
        {!scale && canEdit && (
          <section className="space-y-3 rounded-lg border border-zinc-800 bg-black/40 p-4">
            <p className="text-sm text-zinc-400">Nenhuma escala neste dia. Crie para começar.</p>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Título (ex.: Escala operacional)"
              className="w-full rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100"
            />
            <button
              type="button"
              disabled={busy || !title.trim()}
              onClick={() => onCreateScale(title.trim())}
              className="w-full rounded bg-zinc-100 py-2 text-sm font-medium text-zinc-900 disabled:opacity-40"
            >
              Criar escala
            </button>
          </section>
        )}
        {!scale && !canEdit && <p className="text-sm text-zinc-500">Sem escala publicada para este dia.</p>}

        {scale && (
          <>
            <div className="mb-4 flex flex-wrap gap-2">
              <h3 className="flex-1 text-base font-semibold text-zinc-100">
                {scale.title}
                {scale.current_version_number != null && (
                  <span className="ml-2 rounded border border-zinc-700 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-zinc-400">
                    v{scale.current_version_number}
                  </span>
                )}
              </h3>
              {scale.status === "PUBLISHED" && !formOpen && (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => setExportOpen(true)}
                  className="inline-flex items-center gap-1 rounded border border-sky-800/60 bg-sky-950/40 px-3 py-1 text-xs font-medium text-sky-300"
                >
                  <Share2 className="h-3 w-3" />
                  Mensagem
                </button>
              )}
              {canEdit && (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => setPublishPreviewOpen(true)}
                  className="rounded border border-emerald-700/60 bg-emerald-950/40 px-3 py-1 text-xs font-medium text-emerald-300"
                  title="Preview da mensagem → publicar"
                >
                  {scale.status === "PUBLISHED" ? "Republicar" : "Publicar Escala"}
                </button>
              )}
              {canEdit && scale.status === "PUBLISHED" && (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => {
                    if (
                      window.confirm(
                        "Despublicar esta escala? Escalas DEJEM do Mapa Força voltam para pronta p/ mapa. O histórico de versões é preservado.",
                      )
                    ) {
                      onUnpublish(scale.id);
                    }
                  }}
                  className="rounded border border-amber-800/60 bg-amber-950/30 px-3 py-1 text-xs font-medium text-amber-200"
                >
                  Despublicar
                </button>
              )}
              {canEdit && !formOpen && (
                <button
                  type="button"
                  disabled={busy}
                  onClick={openAddForm}
                  className="rounded border border-zinc-600 px-3 py-1 text-xs font-medium text-zinc-200"
                >
                  + Equipe
                </button>
              )}
              {canEdit && !formOpen && (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => {
                    const label =
                      scale.status === "DRAFT"
                        ? `Excluir o rascunho "${scale.title}"?`
                        : `Excluir a escala "${scale.title}"? Esta ação não pode ser desfeita.`;
                    if (window.confirm(label)) onDeleteScale(scale.id);
                  }}
                  className="inline-flex items-center gap-1 rounded border border-red-900/50 bg-red-950/30 px-3 py-1 text-xs font-medium text-red-300 hover:bg-red-950/50"
                >
                  <Trash2 className="h-3 w-3" />
                  Excluir escala
                </button>
              )}
            </div>

            {canEdit && onUpdateScale && (
              <section className="mb-4 space-y-2 rounded-lg border border-zinc-800 bg-zinc-900/40 p-3">
                <label className="block text-[10px] uppercase tracking-wider text-zinc-500">
                  Fardamento (mensagem operacional)
                  <input
                    value={fardamentoDraft}
                    onChange={(e) => setFardamentoDraft(e.target.value)}
                    onBlur={() => {
                      const next = fardamentoDraft.trim() || null;
                      if (next !== (scale.fardamento ?? null)) {
                        onUpdateScale(scale.id, { fardamento: next });
                      }
                    }}
                    placeholder="Ex.: 5º Uniforme"
                    className="mt-1 w-full rounded border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-sm text-zinc-100"
                  />
                </label>
                <label className="block text-[10px] uppercase tracking-wider text-zinc-500">
                  Observações
                  <textarea
                    value={obsDraft}
                    onChange={(e) => setObsDraft(e.target.value)}
                    onBlur={() => {
                      const next = obsDraft.trim() || null;
                      if (next !== (scale.description ?? null)) {
                        onUpdateScale(scale.id, { description: next });
                      }
                    }}
                    rows={2}
                    placeholder="Opcional — aparece no final da mensagem"
                    className="mt-1 w-full resize-none rounded border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-sm text-zinc-100"
                  />
                </label>
              </section>
            )}

            {formOpen && canEdit && (
              <section className="mb-4 space-y-3 rounded-lg border border-amber-900/40 bg-amber-950/20 p-4">
                <p className="text-xs font-semibold uppercase tracking-wider text-amber-200/90">
                  {isEdit ? "Editar equipe" : "Nova equipe"}
                </p>
                <div className="flex gap-2">
                  {(["FT", "ROCAM"] as ScaleModality[]).map((m) => (
                    <button
                      key={m}
                      type="button"
                      disabled={isEdit}
                      onClick={() => {
                        setModality(m);
                        setVehicleId("");
                        setRoleAssignments(emptyRoleAssignments(m));
                        setRoleBikes({});
                      }}
                      className={`flex-1 rounded py-1.5 text-xs font-semibold ${modality === m ? "bg-zinc-100 text-zinc-900" : "border border-zinc-700 text-zinc-400"} ${isEdit ? "opacity-60" : ""}`}
                    >
                      {m}
                    </button>
                  ))}
                </div>
                {modality === "FT" && (
                  <select
                    value={vehicleId}
                    onChange={(e) => setVehicleId(e.target.value ? Number(e.target.value) : "")}
                    className="w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-2 text-sm"
                  >
                    <option value="">Viatura FT (obrigatória)</option>
                    {ftVehicles.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.prefixo} — {v.placa}
                      </option>
                    ))}
                  </select>
                )}
                <MissionPresetSelect
                  modality={modality}
                  preset={missionPreset}
                  custom={missionCustom}
                  onPresetChange={setMissionPreset}
                  onCustomChange={setMissionCustom}
                  label="Empenho"
                />
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Observações (opcional)"
                  rows={2}
                  className="w-full rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm"
                />
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="datetime-local"
                    value={startAt}
                    onChange={(e) => setStartAt(e.target.value)}
                    className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-xs"
                  />
                  <input
                    type="datetime-local"
                    value={endAt}
                    onChange={(e) => setEndAt(e.target.value)}
                    className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-xs"
                  />
                </div>

                {detail?.staff_roster && (
                  <div className="border-t border-zinc-800/80 pt-3">
                    <p className="mb-2 text-xs uppercase tracking-wider text-zinc-500">
                      Funções da equipe ({teamRoleList.length})
                    </p>

                    <div className="mb-3 rounded-lg border border-zinc-800/80 bg-black/30 px-3 py-2.5">
                      <div className="flex flex-wrap gap-x-4 gap-y-1.5 text-[11px]">
                        <span className="text-zinc-200">
                          Disponíveis:{" "}
                          <span className="font-semibold text-zinc-50">{rosterSummary.disponiveis}</span>
                        </span>
                        <span className="text-emerald-400/90">
                          Em serviço: <span className="font-semibold">{rosterSummary.emServico}</span>
                        </span>
                        {rosterSummary.folga > 0 && (
                          <span className="text-sky-400/90">
                            Folga: <span className="font-semibold">{rosterSummary.folga}</span>
                          </span>
                        )}
                        {rosterSummary.ds > 0 && (
                          <span className="text-cyan-400/90">
                            DS: <span className="font-semibold">{rosterSummary.ds}</span>
                          </span>
                        )}
                        {rosterSummary.ferias > 0 && (
                          <span className="text-violet-400/90">
                            Férias: <span className="font-semibold">{rosterSummary.ferias}</span>
                          </span>
                        )}
                        {rosterSummary.lp > 0 && (
                          <span className="text-orange-400/90">
                            LP: <span className="font-semibold">{rosterSummary.lp}</span>
                          </span>
                        )}
                        {rosterSummary.licenca > 0 && (
                          <span className="text-amber-400/90">
                            Licença: <span className="font-semibold">{rosterSummary.licenca}</span>
                          </span>
                        )}
                        {rosterSummary.outros > 0 && (
                          <span className="text-zinc-400">
                            Outros: <span className="font-semibold">{rosterSummary.outros}</span>
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="mb-2">
                      <label
                        htmlFor="scale-platoon-filter"
                        className="mb-1 block text-[10px] font-medium uppercase tracking-wider text-zinc-500"
                      >
                        Pelotão
                      </label>
                      <select
                        id="scale-platoon-filter"
                        value={platoonFilter}
                        disabled={platoonFilterLocked}
                        onChange={(e) => setPlatoonFilter(e.target.value as PlatoonFilter)}
                        className="w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1.5 text-xs text-zinc-100 disabled:cursor-not-allowed disabled:opacity-70"
                      >
                        {platoonFilterLocked ? (
                          <option value={platoonFilter}>
                            {platoonFilter === "ALL"
                              ? "Todos"
                              : ORGANIZATIONAL_UNIT_SECTION_LABELS[platoonFilter]}
                          </option>
                        ) : (
                          <>
                            <option value="ALL">Todos</option>
                            {ORGANIZATIONAL_UNIT_ORDER.map((unit) => (
                              <option key={unit} value={unit}>
                                {ORGANIZATIONAL_UNIT_SECTION_LABELS[unit]}
                              </option>
                            ))}
                          </>
                        )}
                      </select>
                    </div>

                    <div className="space-y-3">
                      {teamRoleList.map((role) => {
                        const currentUid = roleAssignments[role];
                        let options = filteredAvailableRoster.filter((s) => {
                          const free =
                            isUserAvailable(s.user_id, usage) || selectedMembers.includes(s.user_id);
                          if (typeof currentUid === "number" && s.user_id === currentUid) return true;
                          return free && !selectedMembers.includes(s.user_id);
                        });
                        if (typeof currentUid === "number" && !options.some((s) => s.user_id === currentUid)) {
                          const current = (detail?.staff_roster ?? []).find((s) => s.user_id === currentUid);
                          if (current) options = [current, ...options];
                        }
                        const motoOptions =
                          modality === "ROCAM" && typeof currentUid === "number"
                            ? filterRoCamMotos(
                                roCamMotos,
                                usage,
                                typeof roleBikes[role] === "number" ? roleBikes[role] : null,
                              )
                            : [];
                        return (
                          <div key={role} className="space-y-1.5">
                            <label className="block text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
                              {role}
                            </label>
                            <select
                              value={currentUid === "" ? "" : String(currentUid)}
                              onChange={(e) => {
                                const raw = e.target.value;
                                const nextUid = raw ? Number(raw) : "";
                                setRoleAssignments((prev) => setRoleUser(prev, role, nextUid));
                                if (nextUid === "") {
                                  setRoleBikes((prev) => ({ ...prev, [role]: "" }));
                                }
                              }}
                              className="w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-2 text-sm text-zinc-100"
                            >
                              <option value="">Selecionar policial</option>
                              {options.map((s) => (
                                <option key={s.user_id} value={s.user_id}>
                                  {s.patente} {s.nome_guerra}
                                </option>
                              ))}
                            </select>
                            {modality === "ROCAM" && typeof currentUid === "number" && (
                              <select
                                className="w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1.5 text-xs"
                                value={
                                  roleBikes[role] === "" || roleBikes[role] == null
                                    ? ""
                                    : String(roleBikes[role])
                                }
                                onChange={(e) =>
                                  setRoleBikes((prev) => ({
                                    ...prev,
                                    [role]: e.target.value ? Number(e.target.value) : "",
                                  }))
                                }
                              >
                                <option value="">Moto (obrigatória)</option>
                                {motoOptions.map((v) => (
                                  <option key={v.id} value={v.id}>
                                    {v.prefixo}
                                  </option>
                                ))}
                              </select>
                            )}
                          </div>
                        );
                      })}
                    </div>

                    <>
                      <div
                        className="my-3 flex items-center gap-3"
                        role="separator"
                        aria-label="Separador entre disponível e indisponíveis"
                      >
                        <div className="h-px flex-1 bg-zinc-800" />
                        <span className="text-[9px] font-semibold uppercase tracking-[0.25em] text-zinc-600">
                          Indisponíveis
                        </span>
                        <div className="h-px flex-1 bg-zinc-800" />
                      </div>
                      <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-[0.2em] text-amber-400/80">
                        Indisponíveis
                      </p>
                      <p className="mb-2 text-[10px] text-zinc-600">
                        Informativo — não podem ser selecionados para equipes nesta data.
                      </p>
                      <ul className="max-h-36 space-y-1 overflow-y-auto">
                        {awayRoster.length === 0 ? (
                          <li className="px-2 py-1 text-xs text-zinc-600">Nenhum policial indisponível nesta data.</li>
                        ) : (
                          awayRoster.map((s) => (
                            <li
                              key={s.user_id}
                              className="flex items-center justify-between rounded px-2 py-1.5 text-sm text-zinc-500"
                            >
                              <span>
                                {s.patente} {s.nome_guerra}
                              </span>
                              <span className="flex flex-wrap justify-end gap-1">
                                {s.absences.map((a) => (
                                  <span
                                    key={a.kind}
                                    className={`rounded px-1 text-[9px] font-semibold uppercase ring-1 ${absenceBadgeClass(
                                      absenceDisplayLabel(a.kind, a.label) === "DS" ? "DS" : a.kind,
                                    )}`}
                                  >
                                    {absenceDisplayLabel(a.kind, a.label)}
                                  </span>
                                ))}
                              </span>
                            </li>
                          ))
                        )}
                      </ul>
                    </>
                  </div>
                )}

                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={resetForm}
                    className="flex-1 rounded border border-zinc-700 py-2 text-sm text-zinc-400"
                  >
                    Cancelar
                  </button>
                  <button
                    type="button"
                    disabled={
                      busy ||
                      selectedMembers.length === 0 ||
                      !missionName ||
                      (modality === "FT" && vehicleId === "") ||
                      (modality === "ROCAM" &&
                        teamRoleList.some(
                          (role) =>
                            typeof roleAssignments[role] === "number" && !roleBikes[role],
                        ))
                    }
                    onClick={submitForm}
                    className="flex-1 rounded bg-amber-600/90 py-2 text-sm font-medium text-zinc-950 disabled:opacity-40"
                  >
                    {isEdit ? "Salvar alterações" : "Salvar equipe"}
                  </button>
                </div>
              </section>
            )}

            <ul className="space-y-3">
              {scale.teams.map((team) => (
                <li key={team.id} className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="text-xs font-bold uppercase tracking-wider text-zinc-500">{team.modality}</p>
                      <p className="mt-1 font-semibold text-zinc-100">{team.mission_name}</p>
                      <p className="mt-1 text-xs text-zinc-400">
                        {formatDt(team.start_datetime)} → {formatDt(team.end_datetime)}
                      </p>
                      {team.modality === "FT" && team.vehicle_prefixo && (
                        <p className="mt-1 font-mono text-xs text-zinc-300">Viatura {team.vehicle_prefixo}</p>
                      )}
                      {team.notes && <p className="mt-1 text-xs text-zinc-500">{team.notes}</p>}
                    </div>
                    {canEdit && (
                      <div className="flex shrink-0 flex-col items-end gap-1">
                        <button
                          type="button"
                          disabled={busy || formOpen}
                          onClick={() => openEditForm(team)}
                          className="inline-flex items-center gap-1 text-xs text-zinc-300 hover:text-white"
                        >
                          <Pencil className="h-3 w-3" />
                          Editar
                        </button>
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => onRemoveTeam(team.id)}
                          className="text-xs text-red-400 hover:text-red-300"
                        >
                          Remover
                        </button>
                      </div>
                    )}
                  </div>
                  <ul className="mt-3 space-y-1.5 border-t border-zinc-800/80 pt-3">
                    {sortMembersByRole(team.modality, team.members).map((m) => (
                      <li key={m.id} className="text-sm text-zinc-200">
                        {m.role_label && (
                          <span className="mr-2 text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
                            {m.role_label}
                          </span>
                        )}
                        {team.modality === "ROCAM" ? (
                          <span>
                            {m.patente} {m.nome_guerra}
                            <span className="text-zinc-500"> → </span>
                            <span className="font-mono text-xs text-zinc-400">
                              Moto {m.assigned_vehicle_prefixo ?? "—"}
                            </span>
                          </span>
                        ) : (
                          <span>
                            {m.patente} {m.nome_guerra}
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>

            {dejemBlocks.length > 0 && (
              <section className="mt-6 space-y-3 border-t border-zinc-800 pt-5">
                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.2em] text-zinc-500">DEJEM</p>
                  {scale.status === "DRAFT" && (
                    <p className="mt-1 text-[11px] text-zinc-500">
                      Prévia — serão incorporadas ao Mapa Força ao publicar.
                    </p>
                  )}
                </div>
                <ul className="space-y-3">
                  {dejemBlocks.map((block) => (
                    <li
                      key={block.shift_id}
                      className="rounded-lg border border-violet-900/40 bg-violet-950/20 p-4"
                    >
                      <p className="font-semibold tracking-wide text-violet-100">{block.title}</p>
                      <p className="mt-0.5 text-xs tabular-nums text-zinc-400">
                        {block.start_time.slice(0, 5)} → {block.end_time.slice(0, 5)}
                      </p>
                      {block.vehicle_prefixo && (
                        <p className="mt-1 font-mono text-xs text-zinc-300">{block.vehicle_prefixo}</p>
                      )}
                      <ul className="mt-3 space-y-1 border-t border-violet-900/30 pt-3">
                        {block.members.map((m) => (
                          <li key={m.user_id} className="text-sm text-zinc-200">
                            {m.patente} {m.nome_guerra}
                          </li>
                        ))}
                      </ul>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            <ScaleVersionsPanel
              key={`${scale.id}-${scale.current_version_number ?? 0}-${scale.updated_at}`}
              scaleId={scale.id}
            />
          </>
        )}
      </div>

      <ScaleExportModal
        open={exportOpen}
        scaleId={scale?.id ?? null}
        scaleTitle={scale?.title}
        onClose={() => setExportOpen(false)}
      />
      <ScalePublishPreviewModal
        open={publishPreviewOpen}
        scaleId={scale?.id ?? null}
        scaleTitle={scale?.title}
        initialDescription={scale?.description}
        busy={busy}
        onClose={() => setPublishPreviewOpen(false)}
        onPublish={() => {
          if (scale) {
            onPublish(scale.id);
            setPublishPreviewOpen(false);
          }
        }}
        onSaveObservations={async (description) => {
          if (!scale || !onUpdateScale) return;
          await onUpdateScale(scale.id, { description });
        }}
      />
    </aside>
  );
}

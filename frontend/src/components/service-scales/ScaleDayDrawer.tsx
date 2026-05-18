import { useEffect, useMemo, useState } from "react";
import { Pencil, Share2, Trash2, X } from "lucide-react";
import { ScaleExportModal } from "./ScaleExportModal";
import {
  FT_MISSION_PRESETS,
  ROCAM_MISSION_PRESETS,
  type ScaleDayDetailResponse,
  type ScaleModality,
  type ScaleTeamMemberInput,
  type ScaleTeamPublic,
} from "@/types/serviceScale";
import { absenceBadgeClass, scaleStatusBadgeClass, scaleStatusLabel } from "./statusStyles";
import {
  filterFtVehicles,
  filterRoCamMotos,
  gatherScaleUsage,
  isUserAvailable,
} from "./scaleAvailability";

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

function missionToPreset(mission: string, modality: ScaleModality): { preset: string; custom: string } {
  const presets = modality === "FT" ? FT_MISSION_PRESETS : ROCAM_MISSION_PRESETS;
  if ((presets as readonly string[]).includes(mission)) return { preset: mission, custom: "" };
  return { preset: "__custom__", custom: mission };
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
  onPublish: (scaleId: number) => void;
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
  onPublish,
  onAddTeam,
  onEditTeam,
  onRemoveTeam,
  onDeleteScale,
}: Props) {
  const scale = detail?.scale ?? null;
  const [title, setTitle] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editingTeam, setEditingTeam] = useState<ScaleTeamPublic | null>(null);
  const [modality, setModality] = useState<ScaleModality>("FT");
  const [vehicleId, setVehicleId] = useState<number | "">("");
  const [missionPreset, setMissionPreset] = useState("");
  const [missionCustom, setMissionCustom] = useState("");
  const [notes, setNotes] = useState("");
  const [startAt, setStartAt] = useState(() => toLocalInputFromDate(isoDate, 6));
  const [endAt, setEndAt] = useState(() => toLocalInputFromDate(isoDate, 18));
  const [selectedMembers, setSelectedMembers] = useState<number[]>([]);
  const [roCamBikes, setRoCamBikes] = useState<Record<number, number>>({});
  const [exportOpen, setExportOpen] = useState(false);

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

  const missionName = missionPreset === "__custom__" ? missionCustom.trim() : missionPreset;
  const maxMembers = modality === "FT" ? 4 : 3;
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
    setSelectedMembers([]);
    setRoCamBikes({});
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
    setSelectedMembers(team.members.map((m) => m.user_id));
    const bikes: Record<number, number> = {};
    for (const m of team.members) {
      if (m.assigned_vehicle_id) bikes[m.user_id] = m.assigned_vehicle_id;
    }
    setRoCamBikes(bikes);
  };

  useEffect(() => {
    if (!open) resetForm();
  }, [open, isoDate]);

  const toggleMember = (userId: number) => {
    setSelectedMembers((prev) => {
      if (prev.includes(userId)) return prev.filter((id) => id !== userId);
      if (prev.length >= maxMembers) return prev;
      return [...prev, userId];
    });
  };

  const buildPayload = (): TeamFormPayload | null => {
    if (!missionName || selectedMembers.length === 0) return null;
    if (modality === "FT" && vehicleId === "") return null;
    if (modality === "ROCAM" && selectedMembers.some((uid) => !roCamBikes[uid])) return null;

    const members: ScaleTeamMemberInput[] = selectedMembers.map((uid) => ({
      user_id: uid,
      assigned_vehicle_id: modality === "ROCAM" ? roCamBikes[uid]! : null,
    }));

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
              <h3 className="flex-1 text-base font-semibold text-zinc-100">{scale.title}</h3>
              {scale.status === "PUBLISHED" && !formOpen && (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => setExportOpen(true)}
                  className="inline-flex items-center gap-1 rounded border border-sky-800/60 bg-sky-950/40 px-3 py-1 text-xs font-medium text-sky-300"
                >
                  <Share2 className="h-3 w-3" />
                  Exportar
                </button>
              )}
              {canEdit && scale.status === "DRAFT" && (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => onPublish(scale.id)}
                  className="rounded border border-emerald-700/60 bg-emerald-950/40 px-3 py-1 text-xs font-medium text-emerald-300"
                >
                  Publicar
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
                        setSelectedMembers([]);
                        setRoCamBikes({});
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
                <select
                  value={missionPreset}
                  onChange={(e) => setMissionPreset(e.target.value)}
                  className="w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-2 text-sm"
                >
                  <option value="">Empenho</option>
                  {(modality === "FT" ? FT_MISSION_PRESETS : ROCAM_MISSION_PRESETS).map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                  <option value="__custom__">Personalizado…</option>
                </select>
                {missionPreset === "__custom__" && (
                  <input
                    value={missionCustom}
                    onChange={(e) => setMissionCustom(e.target.value)}
                    placeholder="Empenho customizado"
                    className="w-full rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm"
                  />
                )}
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
                      Efetivo (máx. {maxMembers})
                    </p>
                    <ul className="max-h-48 space-y-1 overflow-y-auto">
                      {detail.staff_roster.map((s) => {
                        const available = isUserAvailable(s.user_id, usage) || selectedMembers.includes(s.user_id);
                        const on = selectedMembers.includes(s.user_id);
                        const motoOptions = filterRoCamMotos(roCamMotos, usage, roCamBikes[s.user_id]);
                        return (
                          <li key={s.user_id} className={!available ? "opacity-40" : ""}>
                            <button
                              type="button"
                              disabled={!available && !on}
                              onClick={() => available && toggleMember(s.user_id)}
                              className={`flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-sm ${on ? "bg-zinc-800 text-zinc-50" : "text-zinc-300 hover:bg-zinc-900"}`}
                            >
                              <span>
                                {s.patente} {s.nome_guerra}
                              </span>
                              <span className="flex gap-1">
                                {!available && !on && (
                                  <span className="rounded px-1 text-[9px] uppercase text-zinc-500">Em outra equipe</span>
                                )}
                                {s.absences.map((a) => (
                                  <span
                                    key={a.kind}
                                    className={`rounded px-1 text-[9px] font-semibold uppercase ring-1 ${absenceBadgeClass(a.kind)}`}
                                  >
                                    {a.label}
                                  </span>
                                ))}
                              </span>
                            </button>
                            {modality === "ROCAM" && on && (
                              <select
                                className="mt-1 w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-xs"
                                value={roCamBikes[s.user_id] ?? ""}
                                onChange={(e) =>
                                  setRoCamBikes((prev) => ({
                                    ...prev,
                                    [s.user_id]: Number(e.target.value),
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
                          </li>
                        );
                      })}
                    </ul>
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
                      (modality === "ROCAM" && selectedMembers.some((uid) => !roCamBikes[uid]))
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
                    {team.members.map((m) => (
                      <li key={m.id} className="text-sm text-zinc-200">
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
          </>
        )}
      </div>

      <ScaleExportModal
        open={exportOpen}
        scaleId={scale?.id ?? null}
        scaleTitle={scale?.title}
        onClose={() => setExportOpen(false)}
      />
    </aside>
  );
}

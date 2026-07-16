import { useEffect, useState } from "react";
import { X } from "lucide-react";
import type { User } from "@/types";
import type { Vehicle } from "@/types/vehicle";
import type {
  DejemParticipantAdminRow,
  DejemShiftCreatePayload,
  DejemShiftDayDetail,
  DejemShiftPublic,
  DejemShiftStatus,
  DejemShiftTemplatePublic,
  DejemShiftType,
  DejemShiftUpdatePayload,
  ParticipationType,
} from "@/types/dejem";
import {
  DEJEM_SHIFT_TYPE_LABELS,
  PARTICIPATION_TYPE_LABELS,
  dejemTimeInputValue,
  formatDejemTime,
} from "@/types/dejem";
import { dejemShiftStatusBadgeClass, dejemShiftStatusLabel } from "./statusStyles";

function formatHeaderDate(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString("pt-BR", {
    weekday: "long",
    day: "2-digit",
    month: "long",
  });
}

function activeVehicles(vehicles: Vehicle[]): Vehicle[] {
  return vehicles
    .filter((v) => v.status === "OPERANDO" || v.status === "RESERVA")
    .slice()
    .sort((a, b) => a.prefixo.localeCompare(b.prefixo, "pt-BR"));
}

type FormState = {
  start_time: string;
  end_time: string;
  shift_type: DejemShiftType;
  capacity: number;
  status: DejemShiftStatus;
  templateId: string;
  vehicle_id: string;
};

const emptyForm = (): FormState => ({
  start_time: "04:55",
  end_time: "12:55",
  shift_type: "FT",
  capacity: 4,
  status: "OPEN",
  templateId: "",
  vehicle_id: "",
});

interface Props {
  open: boolean;
  isoDate: string;
  detail: DejemShiftDayDetail | null;
  canEdit: boolean;
  busy: boolean;
  templates: DejemShiftTemplatePublic[];
  vehicles: Vehicle[];
  monthId: number | null;
  efetivo: User[];
  participantsByShift: Record<number, DejemParticipantAdminRow[]>;
  onClose: () => void;
  onCreate: (payload: DejemShiftCreatePayload) => Promise<void>;
  onUpdate: (shiftId: number, payload: DejemShiftUpdatePayload) => Promise<void>;
  onDelete: (shiftId: number) => Promise<void>;
  onLoadParticipants: (shiftId: number) => Promise<void>;
  onAddParticipant: (
    shiftId: number,
    userId: number,
    participationType: ParticipationType,
  ) => Promise<void>;
  onRemoveParticipant: (shiftId: number, userId: number) => Promise<void>;
  onCloseShift: (shiftId: number) => Promise<void>;
}

export function DejemShiftDayDrawer({
  open,
  isoDate,
  detail,
  canEdit,
  busy,
  templates,
  vehicles,
  monthId,
  efetivo,
  participantsByShift,
  onClose,
  onCreate,
  onUpdate,
  onDelete,
  onLoadParticipants,
  onAddParticipant,
  onRemoveParticipant,
  onCloseShift,
}: Props) {
  const [creating, setCreating] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [addUserId, setAddUserId] = useState("");
  const [addType, setAddType] = useState<ParticipationType>("NORMAL");
  const vehicleOptions = activeVehicles(vehicles);

  useEffect(() => {
    if (!open) {
      setCreating(false);
      setEditingId(null);
      setExpandedId(null);
      setForm(emptyForm());
      setAddUserId("");
      setAddType("NORMAL");
    }
  }, [open, isoDate]);

  useEffect(() => {
    if (expandedId != null) {
      void onLoadParticipants(expandedId);
    }
  }, [expandedId, onLoadParticipants]);

  if (!open) return null;

  const applyTemplate = (templateId: string) => {
    const t = templates.find((x) => String(x.id) === templateId);
    if (!t) {
      setForm((f) => ({ ...f, templateId }));
      return;
    }
    setForm((f) => ({
      ...f,
      templateId,
      start_time: dejemTimeInputValue(t.start_time),
      end_time: dejemTimeInputValue(t.end_time),
      shift_type: t.shift_type,
      capacity: t.default_capacity,
    }));
  };

  const startCreate = () => {
    setEditingId(null);
    setExpandedId(null);
    setCreating(true);
    setForm(emptyForm());
  };

  const startEdit = (s: DejemShiftPublic) => {
    setCreating(false);
    setExpandedId(null);
    setEditingId(s.id);
    setForm({
      start_time: dejemTimeInputValue(s.start_time),
      end_time: dejemTimeInputValue(s.end_time),
      shift_type: s.shift_type,
      capacity: s.capacity,
      status: s.status,
      templateId: "",
      vehicle_id: s.vehicle_id != null ? String(s.vehicle_id) : "",
    });
  };

  const submitCreate = async () => {
    if (!monthId) return;
    try {
      await onCreate({
        month_id: monthId,
        date: isoDate,
        start_time: form.start_time.length === 5 ? `${form.start_time}:00` : form.start_time,
        end_time: form.end_time.length === 5 ? `${form.end_time}:00` : form.end_time,
        shift_type: form.shift_type,
        capacity: form.capacity,
        status: "OPEN",
        vehicle_id: form.vehicle_id ? Number(form.vehicle_id) : null,
      });
      setCreating(false);
      setForm(emptyForm());
    } catch {
      /* página */
    }
  };

  const submitUpdate = async () => {
    if (editingId == null) return;
    try {
      await onUpdate(editingId, {
        start_time: form.start_time.length === 5 ? `${form.start_time}:00` : form.start_time,
        end_time: form.end_time.length === 5 ? `${form.end_time}:00` : form.end_time,
        shift_type: form.shift_type,
        capacity: form.capacity,
        status: form.status,
        vehicle_id: form.vehicle_id ? Number(form.vehicle_id) : null,
      });
      setEditingId(null);
    } catch {
      /* página */
    }
  };

  const handleVehicleChange = async (shift: DejemShiftPublic, value: string) => {
    const vehicleId = value ? Number(value) : null;
    try {
      await onUpdate(shift.id, { vehicle_id: vehicleId });
    } catch {
      /* página */
    }
  };

  const shifts = detail?.shifts ?? [];

  return (
    <aside className="fixed inset-y-0 right-0 z-50 flex w-full max-w-lg flex-col border-l border-zinc-800 bg-zinc-950 shadow-2xl">
      <header className="flex items-start justify-between gap-3 border-b border-zinc-800 px-5 py-4">
        <div>
          <p className="text-xs uppercase tracking-[0.25em] text-zinc-500">Escalas DEJEM</p>
          <h2 className="mt-1 text-lg font-semibold capitalize text-zinc-50">
            {formatHeaderDate(isoDate)}
          </h2>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg p-2 text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100"
          aria-label="Fechar"
        >
          <X className="h-5 w-5" />
        </button>
      </header>

      <div className="flex-1 overflow-y-auto px-5 py-4">
        {!monthId && (
          <p className="rounded-lg border border-amber-900/50 bg-amber-950/30 px-3 py-2 text-sm text-amber-200">
            Não há mês DEJEM distribuído para esta data.
          </p>
        )}

        <div className="space-y-3">
          {shifts.length === 0 && !creating && (
            <p className="text-sm text-zinc-500">Nenhuma escala neste dia.</p>
          )}

          {shifts.map((s) => {
            const participants = participantsByShift[s.id] ?? [];
            const expanded = expandedId === s.id;
            return (
              <div key={s.id} className="rounded-xl border border-zinc-800 bg-zinc-900/40 px-4 py-3">
                {editingId === s.id ? (
                  <ShiftForm
                    form={form}
                    setForm={setForm}
                    templates={templates}
                    vehicles={vehicleOptions}
                    onApplyTemplate={applyTemplate}
                    showStatus
                    busy={busy}
                    onCancel={() => setEditingId(null)}
                    onSubmit={() => void submitUpdate()}
                    submitLabel="Salvar"
                  />
                ) : (
                  <>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-medium tabular-nums text-zinc-100">
                          {formatDejemTime(s.start_time)} – {formatDejemTime(s.end_time)}
                        </p>
                        <p className="mt-1 text-sm text-zinc-400">
                          {DEJEM_SHIFT_TYPE_LABELS[s.shift_type]} · {s.filled_slots}/{s.capacity}{" "}
                          vagas
                        </p>
                        <p className="mt-1 text-xs text-zinc-500">
                          Viatura:{" "}
                          <span className={s.vehicle_prefixo ? "text-zinc-200" : "text-amber-300"}>
                            {s.vehicle_prefixo ?? "⚠ não definida"}
                          </span>
                        </p>
                      </div>
                      <span
                        className={[
                          "rounded-md px-2 py-0.5 text-[11px] font-medium",
                          dejemShiftStatusBadgeClass(s.status),
                        ].join(" ")}
                      >
                        {dejemShiftStatusLabel(s.status)}
                      </span>
                    </div>

                    {canEdit &&
                      (s.status === "OPEN" ||
                        s.status === "CLOSED" ||
                        s.status === "READY_FOR_MAP") && (
                        <label className="mt-3 block text-xs text-zinc-500">
                          Selecionar viatura
                          <select
                            value={s.vehicle_id != null ? String(s.vehicle_id) : ""}
                            disabled={busy}
                            onChange={(e) => void handleVehicleChange(s, e.target.value)}
                            className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-sm text-zinc-100 disabled:opacity-50"
                          >
                            <option value="">Sem viatura</option>
                            {vehicleOptions.map((v) => (
                              <option key={v.id} value={v.id}>
                                {v.prefixo} — {v.placa} ({v.modalidade} · {v.status})
                              </option>
                            ))}
                          </select>
                          <span className="mt-1 block text-[11px] text-zinc-600">
                            Pode ser a mesma de outras equipes (FT / DEJEM).
                          </span>
                        </label>
                      )}

                    <div className="mt-3 flex flex-wrap gap-2">
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => setExpandedId(expanded ? null : s.id)}
                        className="rounded-md border border-zinc-700 px-2.5 py-1 text-xs text-zinc-300 hover:bg-zinc-900 disabled:opacity-50"
                      >
                        {expanded ? "Ocultar participantes" : "Participantes"}
                      </button>
                      {canEdit && s.status === "OPEN" && (
                        <>
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => startEdit(s)}
                            className="rounded-md border border-zinc-700 px-2.5 py-1 text-xs text-zinc-300 hover:bg-zinc-900 disabled:opacity-50"
                          >
                            Editar
                          </button>
                          <button
                            type="button"
                            disabled={busy || s.filled_slots < 1}
                            onClick={() => {
                              if (!s.vehicle_id) {
                                window.alert(
                                  "Selecione uma viatura antes de fechar a escala DEJEM.",
                                );
                                return;
                              }
                              if (
                                window.confirm(
                                  "Fechar esta escala? Ela ficará pronta para integração ao Mapa Força.",
                                )
                              ) {
                                void onCloseShift(s.id);
                              }
                            }}
                            className="rounded-md border border-zinc-700 px-2.5 py-1 text-xs text-zinc-300 hover:bg-zinc-900 disabled:opacity-50"
                          >
                            Fechar Escala
                          </button>
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => {
                              if (window.confirm("Excluir esta escala?")) void onDelete(s.id);
                            }}
                            className="rounded-md border border-red-900/60 px-2.5 py-1 text-xs text-red-300 hover:bg-red-950/40 disabled:opacity-50"
                          >
                            Excluir
                          </button>
                        </>
                      )}
                    </div>

                    {expanded && (
                      <div className="mt-3 space-y-3 border-t border-zinc-800 pt-3">
                        <p className="text-xs uppercase tracking-wider text-zinc-500">
                          Participantes ({participants.length}/{s.capacity})
                        </p>
                        {participants.length === 0 ? (
                          <p className="text-xs text-zinc-500">Nenhum participante.</p>
                        ) : (
                          <ul className="space-y-2">
                            {participants.map((p) => (
                              <li
                                key={p.id}
                                className="flex items-start justify-between gap-2 rounded-lg border border-zinc-800 bg-zinc-950/50 px-3 py-2 text-xs"
                              >
                                <div>
                                  <p className="font-medium text-zinc-100">
                                    {p.patente} {p.nome_guerra}
                                  </p>
                                  <p className="mt-0.5 text-zinc-500">
                                    {PARTICIPATION_TYPE_LABELS[p.participation_type]} · saldo{" "}
                                    {p.remaining_slots} ·{" "}
                                    {new Date(p.created_at).toLocaleString("pt-BR")}
                                  </p>
                                </div>
                                {canEdit && s.status === "OPEN" && (
                                  <button
                                    type="button"
                                    disabled={busy}
                                    onClick={() => {
                                      if (window.confirm("Remover este participante?")) {
                                        void onRemoveParticipant(s.id, p.user_id);
                                      }
                                    }}
                                    className="shrink-0 text-red-300 hover:text-red-200 disabled:opacity-50"
                                  >
                                    Remover
                                  </button>
                                )}
                              </li>
                            ))}
                          </ul>
                        )}

                        {canEdit && s.status === "OPEN" && (
                          <div className="space-y-2 rounded-lg border border-zinc-800 px-3 py-3">
                            <p className="text-xs font-medium text-zinc-300">
                              Adicionar manualmente
                            </p>
                            <select
                              value={addUserId}
                              onChange={(e) => setAddUserId(e.target.value)}
                              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-xs text-zinc-100"
                            >
                              <option value="">Selecione o policial</option>
                              {efetivo.map((u) => (
                                <option key={u.id} value={u.id}>
                                  {u.patente} {u.nome_guerra}
                                </option>
                              ))}
                            </select>
                            <select
                              value={addType}
                              onChange={(e) =>
                                setAddType(e.target.value as ParticipationType)
                              }
                              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-xs text-zinc-100"
                            >
                              {(Object.keys(PARTICIPATION_TYPE_LABELS) as ParticipationType[]).map(
                                (k) => (
                                  <option key={k} value={k}>
                                    {PARTICIPATION_TYPE_LABELS[k]}
                                  </option>
                                ),
                              )}
                            </select>
                            <button
                              type="button"
                              disabled={busy || !addUserId}
                              onClick={() => {
                                void onAddParticipant(s.id, Number(addUserId), addType).then(() => {
                                  setAddUserId("");
                                  setAddType("NORMAL");
                                });
                              }}
                              className="w-full rounded-md bg-zinc-100 px-2 py-1.5 text-xs font-medium text-zinc-950 hover:bg-white disabled:opacity-50"
                            >
                              Adicionar
                            </button>
                            <p className="text-[10px] text-zinc-500">
                              NORMAL consome saldo. EXTRAORDINARY e SUBSTITUTION não consomem.
                            </p>
                          </div>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>
            );
          })}
        </div>

        {creating && (
          <div className="mt-4 rounded-xl border border-zinc-700 bg-zinc-900/50 px-4 py-3">
            <p className="mb-3 text-sm font-medium text-zinc-200">Nova escala</p>
            <ShiftForm
              form={form}
              setForm={setForm}
              templates={templates}
              vehicles={vehicleOptions}
              onApplyTemplate={applyTemplate}
              showStatus={false}
              busy={busy}
              onCancel={() => setCreating(false)}
              onSubmit={() => void submitCreate()}
              submitLabel="Criar"
            />
          </div>
        )}
      </div>

      {canEdit && monthId && !creating && editingId == null && (
        <footer className="border-t border-zinc-800 px-5 py-4">
          <button
            type="button"
            disabled={busy}
            onClick={startCreate}
            className="w-full rounded-lg bg-zinc-100 px-4 py-2.5 text-sm font-medium text-zinc-950 hover:bg-white disabled:opacity-50"
          >
            + Nova Escala
          </button>
        </footer>
      )}
    </aside>
  );
}

function ShiftForm({
  form,
  setForm,
  templates,
  vehicles,
  onApplyTemplate,
  showStatus,
  busy,
  onCancel,
  onSubmit,
  submitLabel,
}: {
  form: FormState;
  setForm: (fn: (f: FormState) => FormState) => void;
  templates: DejemShiftTemplatePublic[];
  vehicles: Vehicle[];
  onApplyTemplate: (id: string) => void;
  showStatus: boolean;
  busy: boolean;
  onCancel: () => void;
  onSubmit: () => void;
  submitLabel: string;
}) {
  const activeTemplates = templates.filter((t) => t.is_active);

  return (
    <div className="space-y-3 text-sm">
      {activeTemplates.length > 0 && (
        <label className="block">
          <span className="mb-1 block text-zinc-500">Template</span>
          <select
            value={form.templateId}
            onChange={(e) => onApplyTemplate(e.target.value)}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100"
          >
            <option value="">Criar manualmente</option>
            {activeTemplates.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </label>
      )}
      <div className="grid grid-cols-2 gap-3">
        <label className="block">
          <span className="mb-1 block text-zinc-500">Início</span>
          <input
            type="time"
            value={form.start_time}
            onChange={(e) => setForm((f) => ({ ...f, start_time: e.target.value }))}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-zinc-500">Fim</span>
          <input
            type="time"
            value={form.end_time}
            onChange={(e) => setForm((f) => ({ ...f, end_time: e.target.value }))}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100"
          />
        </label>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <label className="block">
          <span className="mb-1 block text-zinc-500">Tipo</span>
          <select
            value={form.shift_type}
            onChange={(e) =>
              setForm((f) => ({ ...f, shift_type: e.target.value as DejemShiftType }))
            }
            className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100"
          >
            {(Object.keys(DEJEM_SHIFT_TYPE_LABELS) as DejemShiftType[]).map((k) => (
              <option key={k} value={k}>
                {DEJEM_SHIFT_TYPE_LABELS[k]}
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="mb-1 block text-zinc-500">Vagas</span>
          <input
            type="number"
            min={0}
            value={form.capacity}
            onChange={(e) => setForm((f) => ({ ...f, capacity: Number(e.target.value) }))}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100"
          />
        </label>
      </div>
      <label className="block">
        <span className="mb-1 block text-zinc-500">Viatura</span>
        <select
          value={form.vehicle_id}
          onChange={(e) => setForm((f) => ({ ...f, vehicle_id: e.target.value }))}
          className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100"
        >
          <option value="">Sem viatura</option>
          {vehicles.map((v) => (
            <option key={v.id} value={v.id}>
              {v.prefixo} — {v.placa} ({v.modalidade})
            </option>
          ))}
        </select>
      </label>
      {showStatus && (
        <label className="block">
          <span className="mb-1 block text-zinc-500">Status</span>
          <select
            value={form.status}
            onChange={(e) =>
              setForm((f) => ({ ...f, status: e.target.value as DejemShiftStatus }))
            }
            className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100"
          >
            <option value="OPEN">Aberta</option>
            <option value="CLOSED">Fechada</option>
            <option value="READY_FOR_MAP">Pronta p/ mapa</option>
            <option value="INTEGRATED">No Mapa Força</option>
            <option value="FINISHED">Finalizada</option>
          </select>
        </label>
      )}
      <div className="flex justify-end gap-2 pt-1">
        <button
          type="button"
          disabled={busy}
          onClick={onCancel}
          className="rounded-lg border border-zinc-700 px-3 py-1.5 text-zinc-300 hover:bg-zinc-900 disabled:opacity-50"
        >
          Cancelar
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={onSubmit}
          className="rounded-lg bg-zinc-100 px-3 py-1.5 font-medium text-zinc-950 hover:bg-white disabled:opacity-50"
        >
          {busy ? "Salvando…" : submitLabel}
        </button>
      </div>
    </div>
  );
}

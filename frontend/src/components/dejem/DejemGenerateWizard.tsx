import { useEffect, useMemo, useState } from "react";
import {
  DEJEM_MONTH_NAMES,
  dejemMonthLabel,
  formatDejemTime,
} from "@/types/dejem";
import type {
  DejemGeneratePreviewAction,
  DejemMonthGeneratePayload,
  DejemMonthGeneratePreview,
  DejemMonthGenerateResult,
  DejemShiftTemplatePublic,
  DejemShiftType,
} from "@/types/dejem";

const WEEKDAY_OPTIONS: { value: number; label: string }[] = [
  { value: 0, label: "Segunda" },
  { value: 1, label: "Terça" },
  { value: 2, label: "Quarta" },
  { value: 3, label: "Quinta" },
  { value: 4, label: "Sexta" },
  { value: 5, label: "Sábado" },
  { value: 6, label: "Domingo" },
];

type Step = 1 | 2 | 3 | 4;
type Phase = "wizard" | "preview" | "result";

interface Props {
  open: boolean;
  initialYear: number;
  initialMonth: number;
  templates: DejemShiftTemplatePublic[];
  busy: boolean;
  onClose: () => void;
  onPreview: (payload: DejemMonthGeneratePayload) => Promise<DejemMonthGeneratePreview>;
  onGenerate: (payload: DejemMonthGeneratePayload) => Promise<DejemMonthGenerateResult>;
  onGoToCalendar: (year: number, month: number) => void;
}

function actionClass(action: DejemGeneratePreviewAction): string {
  if (action === "CREATE") return "text-emerald-300";
  if (action === "REPLACE") return "text-amber-300";
  return "text-zinc-400";
}

function formatDay(isoDate: string): string {
  const [, m, d] = isoDate.split("-");
  return `${d}/${m}`;
}

export function DejemGenerateWizard({
  open,
  initialYear,
  initialMonth,
  templates,
  busy,
  onClose,
  onPreview,
  onGenerate,
  onGoToCalendar,
}: Props) {
  const [phase, setPhase] = useState<Phase>("wizard");
  const [step, setStep] = useState<Step>(1);
  const [year, setYear] = useState(initialYear);
  const [month, setMonth] = useState(initialMonth);
  const [weekdays, setWeekdays] = useState<number[]>([0, 1, 2, 3, 4, 5, 6]);
  const [templateIds, setTemplateIds] = useState<number[]>([]);
  const [replaceExisting, setReplaceExisting] = useState(false);
  const [ignoreHolidays, setIgnoreHolidays] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<DejemMonthGeneratePreview | null>(null);
  const [result, setResult] = useState<DejemMonthGenerateResult | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);

  const [filterDate, setFilterDate] = useState("");
  const [filterType, setFilterType] = useState<"" | DejemShiftType>("");
  const [filterTemplate, setFilterTemplate] = useState<number | "">("");
  const [filterStatus, setFilterStatus] = useState<"" | DejemGeneratePreviewAction>("");

  useEffect(() => {
    if (!open) return;
    setPhase("wizard");
    setStep(1);
    setYear(initialYear);
    setMonth(initialMonth);
    setWeekdays([0, 1, 2, 3, 4, 5, 6]);
    setTemplateIds(templates.filter((t) => t.is_active).map((t) => t.id));
    setReplaceExisting(false);
    setIgnoreHolidays(false);
    setError(null);
    setPreview(null);
    setResult(null);
    setLoadingPreview(false);
    setFilterDate("");
    setFilterType("");
    setFilterTemplate("");
    setFilterStatus("");
  }, [open, initialYear, initialMonth, templates]);

  const activeTemplates = useMemo(
    () => templates.filter((t) => t.is_active),
    [templates],
  );

  const payload = useMemo<DejemMonthGeneratePayload>(
    () => ({
      year,
      month,
      weekdays,
      template_ids: templateIds,
      replace_existing: replaceExisting,
      ignore_holidays: ignoreHolidays,
    }),
    [year, month, weekdays, templateIds, replaceExisting, ignoreHolidays],
  );

  const filteredItems = useMemo(() => {
    if (!preview) return [];
    return preview.items.filter((item) => {
      if (filterDate && item.date !== filterDate) return false;
      if (filterType && item.shift_type !== filterType) return false;
      if (filterTemplate !== "" && item.template_id !== filterTemplate) return false;
      if (filterStatus && item.action !== filterStatus) return false;
      return true;
    });
  }, [preview, filterDate, filterType, filterTemplate, filterStatus]);

  const uniqueDates = useMemo(() => {
    if (!preview) return [] as string[];
    return [...new Set(preview.items.map((i) => i.date))].sort();
  }, [preview]);

  const uniqueTypes = useMemo(() => {
    if (!preview) return [] as DejemShiftType[];
    return [...new Set(preview.items.map((i) => i.shift_type))];
  }, [preview]);

  const uniqueTemplates = useMemo(() => {
    if (!preview) return [] as { id: number; name: string }[];
    const map = new Map<number, string>();
    for (const i of preview.items) map.set(i.template_id, i.template_name);
    return [...map.entries()].map(([id, name]) => ({ id, name }));
  }, [preview]);

  const daysSelectedLabel = useMemo(() => {
    if (!preview) return "";
    if (preview.weekday_labels.length === 7) return "Segunda até Domingo";
    return preview.weekday_labels.join(", ");
  }, [preview]);

  if (!open) return null;

  const toggleWeekday = (d: number) => {
    setWeekdays((prev) =>
      prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d].sort((a, b) => a - b),
    );
  };

  const toggleTemplate = (id: number) => {
    setTemplateIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  };

  const canNext =
    (step === 1 && year >= 2000 && month >= 1 && month <= 12) ||
    (step === 2 && weekdays.length > 0) ||
    (step === 3 && templateIds.length > 0) ||
    step === 4;

  const loadPreview = async () => {
    setError(null);
    setLoadingPreview(true);
    try {
      const res = await onPreview(payload);
      setPreview(res);
      setPhase("preview");
      setFilterDate("");
      setFilterType("");
      setFilterTemplate("");
      setFilterStatus("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao pré-visualizar");
    } finally {
      setLoadingPreview(false);
    }
  };

  const confirm = async () => {
    setError(null);
    try {
      const res = await onGenerate(payload);
      setResult(res);
      setPhase("result");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao gerar escalas");
    }
  };
  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 p-4">
      <div
        className={`flex max-h-[90vh] w-full flex-col rounded-xl border border-zinc-700 bg-zinc-950 shadow-xl ${
          phase === "preview" ? "max-w-3xl" : "max-w-lg"
        }`}
      >
        <header className="border-b border-zinc-800 px-5 py-4">
          <p className="text-xs uppercase tracking-[0.25em] text-zinc-500">Assistente</p>
          <h3 className="mt-1 text-lg font-semibold text-zinc-50">
            {phase === "preview"
              ? "Pré-visualização da geração"
              : phase === "result"
                ? "Geração concluída"
                : "Gerar Escalas do Mês"}
          </h3>
          {phase === "wizard" && (
            <p className="mt-2 text-xs text-zinc-500">Etapa {step} de 4</p>
          )}
          {phase === "preview" && preview && (
            <p className="mt-2 text-xs text-zinc-500">
              Simulação — nenhuma escala será criada até a confirmação
            </p>
          )}
        </header>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {error && (
            <p className="mb-4 rounded-lg border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-200">
              {error}
            </p>
          )}

          {phase === "result" && result && (
            <div className="space-y-3 text-sm">
              <p className="text-base font-medium text-zinc-100">
                {dejemMonthLabel(result.year, result.month)}
              </p>
              <dl className="space-y-2 rounded-lg border border-zinc-800 bg-zinc-900/40 px-4 py-3">
                <div className="flex justify-between gap-4">
                  <dt className="text-zinc-400">Escalas criadas</dt>
                  <dd className="tabular-nums text-zinc-100">{result.created}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-zinc-400">Escalas ignoradas</dt>
                  <dd className="tabular-nums text-zinc-100">{result.ignored}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-zinc-400">Escalas substituídas</dt>
                  <dd className="tabular-nums text-zinc-100">{result.replaced}</dd>
                </div>
                <div className="flex justify-between gap-4 border-t border-zinc-800 pt-2">
                  <dt className="text-zinc-400">Tempo de processamento</dt>
                  <dd className="tabular-nums text-zinc-100">{result.elapsed_ms} ms</dd>
                </div>
              </dl>
            </div>
          )}

          {phase === "preview" && preview && (
            <div className="space-y-5 text-sm">
              <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 px-4 py-3">
                <p className="text-base font-medium text-zinc-100">
                  {dejemMonthLabel(preview.year, preview.month)}
                </p>
                <dl className="mt-3 grid gap-2 sm:grid-cols-2">
                  <div className="flex justify-between gap-3 sm:block">
                    <dt className="text-zinc-500">Dias do mês</dt>
                    <dd className="tabular-nums text-zinc-100">{preview.days_in_month}</dd>
                  </div>
                  <div className="flex justify-between gap-3 sm:block">
                    <dt className="text-zinc-500">Dias selecionados</dt>
                    <dd className="text-zinc-100">
                      {daysSelectedLabel}
                      <span className="ml-1 text-zinc-500">
                        ({preview.selected_days_count} dias)
                      </span>
                    </dd>
                  </div>
                </dl>
                <div className="mt-3 border-t border-zinc-800 pt-3">
                  <p className="mb-1 text-zinc-500">Templates</p>
                  <ul className="space-y-0.5 text-zinc-100">
                    {preview.template_names.map((name) => (
                      <li key={name}>✓ {name}</li>
                    ))}
                  </ul>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-3 border-t border-zinc-800 pt-3">
                  <div>
                    <p className="text-zinc-500">Escalas previstas</p>
                    <p className="text-xl tabular-nums font-semibold text-zinc-50">
                      {preview.create_count + preview.replace_count}
                    </p>
                  </div>
                  <div>
                    <p className="text-zinc-500">Vagas previstas</p>
                    <p className="text-xl tabular-nums font-semibold text-zinc-50">
                      {preview.planned_capacity}
                    </p>
                  </div>
                </div>
              </div>

              {preview.existing_conflicts > 0 && (
                <div className="rounded-lg border border-amber-900/50 bg-amber-950/30 px-4 py-3 text-amber-100">
                  <p>
                    Foram encontradas {preview.existing_conflicts} escalas já existentes.
                  </p>
                  <p className="mt-1 text-amber-200/90">
                    Essas escalas serão:{" "}
                    <strong>
                      {preview.replace_existing
                        ? "substituídas (quando sem participantes)"
                        : "ignoradas"}
                    </strong>
                    .
                  </p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
                <div className="rounded-lg border border-zinc-800 px-3 py-2">
                  <p className="text-xs text-zinc-500">Novas</p>
                  <p className="tabular-nums text-emerald-300">{preview.create_count}</p>
                </div>
                <div className="rounded-lg border border-zinc-800 px-3 py-2">
                  <p className="text-xs text-zinc-500">Ignoradas</p>
                  <p className="tabular-nums text-zinc-300">{preview.ignore_count}</p>
                </div>
                <div className="rounded-lg border border-zinc-800 px-3 py-2">
                  <p className="text-xs text-zinc-500">Substituídas</p>
                  <p className="tabular-nums text-amber-300">{preview.replace_count}</p>
                </div>
                <div className="rounded-lg border border-zinc-800 px-3 py-2">
                  <p className="text-xs text-zinc-500">Vagas criadas</p>
                  <p className="tabular-nums text-zinc-100">{preview.create_capacity}</p>
                </div>
                <div className="rounded-lg border border-zinc-800 px-3 py-2">
                  <p className="text-xs text-zinc-500">Vagas subst.</p>
                  <p className="tabular-nums text-zinc-100">{preview.replace_capacity}</p>
                </div>
              </div>

              <div className="grid gap-2 sm:grid-cols-4">
                <label className="text-xs">
                  <span className="mb-1 block text-zinc-500">Data</span>
                  <select
                    value={filterDate}
                    onChange={(e) => setFilterDate(e.target.value)}
                    className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-zinc-100"
                  >
                    <option value="">Todas</option>
                    {uniqueDates.map((d) => (
                      <option key={d} value={d}>
                        {formatDay(d)}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="text-xs">
                  <span className="mb-1 block text-zinc-500">Tipo</span>
                  <select
                    value={filterType}
                    onChange={(e) => setFilterType(e.target.value as "" | DejemShiftType)}
                    className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-zinc-100"
                  >
                    <option value="">Todos</option>
                    {uniqueTypes.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="text-xs">
                  <span className="mb-1 block text-zinc-500">Template</span>
                  <select
                    value={filterTemplate}
                    onChange={(e) =>
                      setFilterTemplate(e.target.value ? Number(e.target.value) : "")
                    }
                    className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-zinc-100"
                  >
                    <option value="">Todos</option>
                    {uniqueTemplates.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="text-xs">
                  <span className="mb-1 block text-zinc-500">Status</span>
                  <select
                    value={filterStatus}
                    onChange={(e) =>
                      setFilterStatus(e.target.value as "" | DejemGeneratePreviewAction)
                    }
                    className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-zinc-100"
                  >
                    <option value="">Todos</option>
                    <option value="CREATE">Será criada</option>
                    <option value="IGNORE">Será ignorada</option>
                    <option value="REPLACE">Será substituída</option>
                  </select>
                </label>
              </div>

              <div className="overflow-x-auto rounded-lg border border-zinc-800">
                <table className="w-full min-w-[560px] text-left text-xs">
                  <thead className="border-b border-zinc-800 bg-zinc-900/60 text-zinc-500">
                    <tr>
                      <th className="px-3 py-2 font-medium">Data</th>
                      <th className="px-3 py-2 font-medium">Horário</th>
                      <th className="px-3 py-2 font-medium">Tipo</th>
                      <th className="px-3 py-2 font-medium">Capacidade</th>
                      <th className="px-3 py-2 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredItems.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-3 py-6 text-center text-zinc-500">
                          Nenhuma escala no filtro.
                        </td>
                      </tr>
                    ) : (
                      filteredItems.map((item) => (
                        <tr
                          key={`${item.date}-${item.template_id}-${item.start_time}-${item.action}`}
                          className="border-b border-zinc-900/80"
                        >
                          <td className="px-3 py-2 tabular-nums text-zinc-200">
                            {formatDay(item.date)}
                          </td>
                          <td className="px-3 py-2 tabular-nums text-zinc-300">
                            {formatDejemTime(item.start_time)} →{" "}
                            {formatDejemTime(item.end_time)}
                          </td>
                          <td className="px-3 py-2 text-zinc-200">{item.shift_type}</td>
                          <td className="px-3 py-2 text-zinc-300">
                            {item.capacity} vagas
                          </td>
                          <td className={`px-3 py-2 ${actionClass(item.action)}`}>
                            {item.status_label}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-zinc-500">
                Exibindo {filteredItems.length} de {preview.items.length} · preview em{" "}
                {preview.elapsed_ms} ms
              </p>
            </div>
          )}

          {phase === "wizard" && (
            <>
              {step === 1 && (
                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="text-sm">
                    <span className="mb-1 block text-zinc-500">Mês</span>
                    <select
                      value={month}
                      onChange={(e) => setMonth(Number(e.target.value))}
                      className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100"
                    >
                      {DEJEM_MONTH_NAMES.slice(1).map((name, idx) => (
                        <option key={name} value={idx + 1}>
                          {name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="text-sm">
                    <span className="mb-1 block text-zinc-500">Ano</span>
                    <input
                      type="number"
                      min={2000}
                      max={2100}
                      value={year}
                      onChange={(e) => setYear(Number(e.target.value))}
                      className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100"
                    />
                  </label>
                </div>
              )}

              {step === 2 && (
                <div className="space-y-2">
                  <p className="mb-3 text-sm text-zinc-400">
                    Selecione os dias da semana que terão DEJEM.
                  </p>
                  {WEEKDAY_OPTIONS.map((w) => (
                    <label
                      key={w.value}
                      className="flex cursor-pointer items-center gap-3 rounded-lg border border-zinc-800 px-3 py-2 text-sm text-zinc-200 hover:bg-zinc-900/50"
                    >
                      <input
                        type="checkbox"
                        checked={weekdays.includes(w.value)}
                        onChange={() => toggleWeekday(w.value)}
                        className="accent-zinc-200"
                      />
                      {w.label}
                    </label>
                  ))}
                </div>
              )}

              {step === 3 && (
                <div className="space-y-2">
                  <p className="mb-3 text-sm text-zinc-400">
                    Selecione os templates que serão aplicados em cada dia.
                  </p>
                  {activeTemplates.length === 0 ? (
                    <p className="text-sm text-amber-200">
                      Nenhum template ativo. Cadastre templates antes de gerar.
                    </p>
                  ) : (
                    activeTemplates.map((t) => (
                      <label
                        key={t.id}
                        className="flex cursor-pointer items-start gap-3 rounded-lg border border-zinc-800 px-3 py-2 text-sm text-zinc-200 hover:bg-zinc-900/50"
                      >
                        <input
                          type="checkbox"
                          checked={templateIds.includes(t.id)}
                          onChange={() => toggleTemplate(t.id)}
                          className="mt-1 accent-zinc-200"
                        />
                        <span>
                          <span className="font-medium text-zinc-100">{t.name}</span>
                          <span className="mt-0.5 block text-xs text-zinc-500">
                            {t.shift_type} · {formatDejemTime(t.start_time)}–
                            {formatDejemTime(t.end_time)} · {t.default_capacity} vagas
                          </span>
                        </span>
                      </label>
                    ))
                  )}
                </div>
              )}

              {step === 4 && (
                <div className="space-y-5 text-sm">
                  <div>
                    <p className="mb-2 font-medium text-zinc-200">
                      Substituir escalas existentes
                    </p>
                    <p className="mb-3 text-xs text-zinc-500">
                      Se desabilitado, escalas com mesmo dia, horário e tipo não serão
                      recriadas. Com participantes, a escala sempre será ignorada.
                    </p>
                    <div className="space-y-2">
                      <label className="flex cursor-pointer items-center gap-3 text-zinc-200">
                        <input
                          type="radio"
                          name="replace"
                          checked={!replaceExisting}
                          onChange={() => setReplaceExisting(false)}
                          className="accent-zinc-200"
                        />
                        Ignorar existentes
                      </label>
                      <label className="flex cursor-pointer items-center gap-3 text-zinc-200">
                        <input
                          type="radio"
                          name="replace"
                          checked={replaceExisting}
                          onChange={() => setReplaceExisting(true)}
                          className="accent-zinc-200"
                        />
                        Substituir existentes vazias
                      </label>
                    </div>
                  </div>
                  <label className="flex cursor-not-allowed items-center gap-3 text-zinc-500 opacity-70">
                    <input
                      type="checkbox"
                      checked={ignoreHolidays}
                      disabled
                      className="accent-zinc-200"
                    />
                    Ignorar feriados (em breve)
                  </label>
                  <p className="text-xs text-zinc-500">
                    Em seguida será exibida a pré-visualização — nada será gravado ainda.
                  </p>
                </div>
              )}
            </>
          )}
        </div>

        <footer className="flex flex-wrap justify-end gap-2 border-t border-zinc-800 px-5 py-4">
          {phase === "result" && result ? (
            <>
              <button
                type="button"
                onClick={onClose}
                className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-900"
              >
                Fechar
              </button>
              <button
                type="button"
                onClick={() => {
                  onGoToCalendar(result.year, result.month);
                  onClose();
                }}
                className="rounded-lg bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-950 hover:bg-white"
              >
                Ir para o calendário
              </button>
            </>
          ) : phase === "preview" ? (
            <>
              <button
                type="button"
                disabled={busy}
                onClick={onClose}
                className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-900 disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => {
                  setPhase("wizard");
                  setStep(4);
                  setError(null);
                }}
                className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-900 disabled:opacity-50"
              >
                ← Voltar
              </button>
              <button
                type="button"
                disabled={busy || !preview}
                onClick={() => void confirm()}
                className="rounded-lg bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-950 hover:bg-white disabled:opacity-50"
              >
                {busy ? "Gerando…" : "Confirmar Geração"}
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                disabled={busy || loadingPreview}
                onClick={onClose}
                className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-900 disabled:opacity-50"
              >
                Cancelar
              </button>
              {step > 1 && (
                <button
                  type="button"
                  disabled={busy || loadingPreview}
                  onClick={() => setStep((s) => (s - 1) as Step)}
                  className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-900 disabled:opacity-50"
                >
                  Voltar
                </button>
              )}
              {step < 4 ? (
                <button
                  type="button"
                  disabled={!canNext || busy || loadingPreview}
                  onClick={() => setStep((s) => (s + 1) as Step)}
                  className="rounded-lg bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-950 hover:bg-white disabled:opacity-50"
                >
                  Continuar
                </button>
              ) : (
                <button
                  type="button"
                  disabled={!canNext || busy || loadingPreview || templateIds.length === 0}
                  onClick={() => void loadPreview()}
                  className="rounded-lg bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-950 hover:bg-white disabled:opacity-50"
                >
                  {loadingPreview ? "Calculando…" : "Pré-visualizar"}
                </button>
              )}
            </>
          )}
        </footer>
      </div>
    </div>
  );
}

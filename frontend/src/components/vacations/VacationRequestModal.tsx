import { useEffect, useMemo, useState } from "react";
import { ApiError } from "@/services/api";
import { RESTRICTED_ABSENCE_TYPES, type VacationType } from "@/types/vacation";
import { vacationTypeLabel } from "./statusStyles";

interface Props {
  open: boolean;
  defaultStart: string | null;
  onClose: () => void;
  onSubmit: (payload: {
    start_date: string;
    end_date: string;
    vacation_type: VacationType;
    notes?: string | null;
  }) => Promise<void>;
}

const ALL_TYPES: VacationType[] = [
  "FERIAS",
  "LP",
  "LTS",
  "CURSO",
  "ESTAGIO_OPERACIONAL",
  "OUTROS",
];

function inclusiveDays(start: string, end: string): number | null {
  if (!start || !end) return null;
  const a = new Date(start + "T12:00:00");
  const b = new Date(end + "T12:00:00");
  if (Number.isNaN(a.getTime()) || Number.isNaN(b.getTime()) || b < a) return null;
  return Math.round((b.getTime() - a.getTime()) / 86400000) + 1;
}

export function VacationRequestModal({ open, defaultStart, onClose, onSubmit }: Props) {
  const [startDate, setStartDate] = useState(defaultStart ?? "");
  const [endDate, setEndDate] = useState("");
  const [vacationType, setVacationType] = useState<VacationType>("FERIAS");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (open && defaultStart) setStartDate(defaultStart);
  }, [open, defaultStart]);

  const totalDays = useMemo(() => inclusiveDays(startDate, endDate), [startDate, endDate]);
  const isRestricted = RESTRICTED_ABSENCE_TYPES.includes(vacationType);
  const periodValid = isRestricted
    ? totalDays === 15 || totalDays === 30
    : totalDays != null && totalDays >= 1;

  const periodHint = useMemo(() => {
    if (totalDays == null) return "Informe início e fim do período.";
    if (isRestricted) {
      return totalDays === 15 || totalDays === 30
        ? `Período válido: ${totalDays} dias (férias/LP).`
        : `Férias/LP: apenas 15 ou 30 dias (atual: ${totalDays}).`;
    }
    return `Período livre: ${totalDays} dia(s). Sem limite de simultaneidade.`;
  }, [totalDays, isRestricted]);

  if (!open) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    if (!periodValid || !startDate || !endDate) {
      setErr(isRestricted ? "Férias/LP: apenas 15 ou 30 dias." : "Informe um período válido.");
      return;
    }
    setBusy(true);
    try {
      await onSubmit({
        start_date: startDate,
        end_date: endDate,
        vacation_type: vacationType,
        notes: notes.trim() || null,
      });
      setStartDate(defaultStart ?? "");
      setEndDate("");
      setVacationType("FERIAS");
      setNotes("");
      onClose();
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : e instanceof Error ? e.message : "Erro ao solicitar");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-xl border border-zinc-700 bg-zinc-950 p-6 shadow-2xl">
        <header className="flex items-start justify-between gap-2">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.3em] text-zinc-500">Solicitação</p>
            <h3 className="mt-1 text-lg font-semibold text-zinc-50">Novo afastamento</h3>
            <p className="mt-1 text-sm text-zinc-400">
              Férias/LP: 15 ou 30 dias com regra de simultaneidade. Demais tipos: período livre.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded border border-zinc-700 px-2 py-1 text-xs text-zinc-400 hover:text-white"
          >
            Fechar
          </button>
        </header>
        <form className="mt-6 space-y-4" onSubmit={(e) => void handleSubmit(e)}>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="text-xs font-medium text-zinc-400">
              Início
              <input
                type="date"
                required
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="mt-1 w-full rounded-lg border border-zinc-800 bg-black/50 px-3 py-2 text-sm text-zinc-100"
              />
            </label>
            <label className="text-xs font-medium text-zinc-400">
              Fim
              <input
                type="date"
                required
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="mt-1 w-full rounded-lg border border-zinc-800 bg-black/50 px-3 py-2 text-sm text-zinc-100"
              />
            </label>
          </div>
          <p
            className={[
              "text-xs",
              periodValid ? "text-emerald-400/90" : totalDays != null ? "text-amber-200/90" : "text-zinc-500",
            ].join(" ")}
          >
            {periodHint}
          </p>
          <div>
            <p className="text-xs font-medium text-zinc-400">Tipo de afastamento</p>
            <div className="mt-2 max-h-48 space-y-2 overflow-y-auto">
              {ALL_TYPES.map((t) => (
                <label
                  key={t}
                  className="flex cursor-pointer items-center gap-2 rounded-lg border border-zinc-800 bg-black/40 px-3 py-2 text-sm"
                >
                  <input
                    type="radio"
                    name="vt"
                    checked={vacationType === t}
                    onChange={() => setVacationType(t)}
                  />
                  {vacationTypeLabel(t)}
                </label>
              ))}
            </div>
          </div>
          <label className="block text-xs font-medium text-zinc-400">
            Observações (opcional)
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="mt-1 w-full rounded-lg border border-zinc-800 bg-black/50 px-3 py-2 text-sm text-zinc-100"
              placeholder="Ex.: curso na Academia, LTS médico…"
            />
          </label>
          {err && <p className="text-sm text-red-400">{err}</p>}
          <footer className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300"
            >
              Voltar
            </button>
            <button
              type="submit"
              disabled={busy || !periodValid}
              className="rounded-lg border border-emerald-800/80 bg-emerald-950/50 px-4 py-2 text-sm font-medium text-emerald-100 disabled:opacity-50"
            >
              {busy ? "Enviando…" : "Registrar"}
            </button>
          </footer>
        </form>
      </div>
    </div>
  );
}

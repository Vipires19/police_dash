import { X } from "lucide-react";
import type { DejemMyDayDetail, DejemMyShiftCard } from "@/types/dejem";
import { DEJEM_SHIFT_TYPE_LABELS, formatDejemTime } from "@/types/dejem";
import { dejemShiftStatusBadgeClass, dejemShiftStatusLabel } from "./statusStyles";

function formatHeaderDate(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString("pt-BR", {
    weekday: "long",
    day: "2-digit",
    month: "long",
  });
}

interface Props {
  open: boolean;
  isoDate: string;
  detail: DejemMyDayDetail | null;
  busy: boolean;
  remainingSlots: number;
  onClose: () => void;
  onEnroll: (shiftId: number) => Promise<void>;
  onCancel: (shiftId: number) => Promise<void>;
}

export function DejemMyEnrollmentDrawer({
  open,
  isoDate,
  detail,
  busy,
  remainingSlots,
  onClose,
  onEnroll,
  onCancel,
}: Props) {
  if (!open) return null;

  const shifts = detail?.shifts ?? [];

  const actionFor = (s: DejemMyShiftCard) => {
    if (s.status !== "OPEN") {
      return (
        <span className="text-xs text-zinc-500">{dejemShiftStatusLabel(s.status)}</span>
      );
    }
    if (s.i_am_enrolled) {
      return (
        <button
          type="button"
          disabled={busy}
          onClick={() => void onCancel(s.id)}
          className="rounded-md border border-zinc-700 px-2.5 py-1 text-xs text-zinc-300 hover:bg-zinc-900 disabled:opacity-50"
        >
          Cancelar
        </button>
      );
    }
    if (s.available_slots <= 0) {
      return <span className="text-xs font-medium uppercase tracking-wide text-amber-300">Lotada</span>;
    }
    if (remainingSlots <= 0) {
      return <span className="text-xs text-zinc-500">Sem saldo</span>;
    }
    return (
      <button
        type="button"
        disabled={busy}
        onClick={() => void onEnroll(s.id)}
        className="rounded-md bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-950 hover:bg-white disabled:opacity-50"
      >
        Participar
      </button>
    );
  };

  return (
    <aside className="fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col border-l border-zinc-800 bg-zinc-950 shadow-2xl">
      <header className="flex items-start justify-between gap-3 border-b border-zinc-800 px-5 py-4">
        <div>
          <p className="text-xs uppercase tracking-[0.25em] text-zinc-500">Inscrição</p>
          <h2 className="mt-1 text-lg font-semibold capitalize text-zinc-50">
            {formatHeaderDate(isoDate)}
          </h2>
          <p className="mt-1 text-xs text-zinc-500">
            Saldo disponível: <span className="tabular-nums text-zinc-300">{remainingSlots}</span>
          </p>
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
        {shifts.length === 0 ? (
          <p className="text-sm text-zinc-500">Nenhuma escala neste dia.</p>
        ) : (
          <div className="space-y-3">
            {shifts.map((s) => (
              <div
                key={s.id}
                className="flex items-start justify-between gap-3 rounded-xl border border-zinc-800 bg-zinc-900/40 px-4 py-3"
              >
                <div>
                  <p className="font-medium tabular-nums text-zinc-100">
                    {formatDejemTime(s.start_time)}
                  </p>
                  <p className="mt-0.5 text-sm text-zinc-400">
                    {DEJEM_SHIFT_TYPE_LABELS[s.shift_type]}
                  </p>
                  <p className="mt-1 text-xs text-zinc-500">
                    {s.filled_slots} / {s.capacity} vagas
                  </p>
                  {s.i_am_enrolled && (
                    <p className="mt-1 text-xs text-emerald-400">Você está inscrito</p>
                  )}
                </div>
                <div className="flex flex-col items-end gap-2">
                  <span
                    className={[
                      "rounded-md px-2 py-0.5 text-[11px] font-medium",
                      dejemShiftStatusBadgeClass(s.status),
                    ].join(" ")}
                  >
                    {dejemShiftStatusLabel(s.status)}
                  </span>
                  {actionFor(s)}
                </div>
              </div>
            ))}
          </div>
        )}
        <p className="mt-4 text-xs leading-relaxed text-zinc-500">
          Os nomes dos demais participantes não são exibidos. Apenas a ocupação das vagas.
        </p>
      </div>
    </aside>
  );
}

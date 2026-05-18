import type { VacationCalendarDay } from "@/types/vacation";
import { vacationStatusCellClass } from "./statusStyles";

const WEEK = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];

function mondayOffset(year: number, month: number): number {
  const js = new Date(year, month - 1, 1).getDay();
  return js === 0 ? 6 : js - 1;
}

function daysInMonth(year: number, month: number): number {
  return new Date(year, month, 0).getDate();
}

interface Props {
  year: number;
  month: number;
  days: VacationCalendarDay[];
  selected: string | null;
  onSelect: (isoDate: string) => void;
  onPrev: () => void;
  onNext: () => void;
}

export function VacationMonthlyCalendar({
  year,
  month,
  days,
  selected,
  onSelect,
  onPrev,
  onNext,
}: Props) {
  const byDate = new Map(days.map((d) => [d.date, d]));
  const dim = daysInMonth(year, month);
  const pad = mondayOffset(year, month);
  const cells: ({ kind: "empty" } | { kind: "day"; n: number; iso: string })[] = [];
  for (let i = 0; i < pad; i++) cells.push({ kind: "empty" });
  for (let n = 1; n <= dim; n++) {
    const iso = `${year}-${String(month).padStart(2, "0")}-${String(n).padStart(2, "0")}`;
    cells.push({ kind: "day", n, iso });
  }
  while (cells.length % 7 !== 0) cells.push({ kind: "empty" });

  const title = new Date(year, month - 1, 1).toLocaleString("pt-BR", { month: "long", year: "numeric" });

  return (
    <div className="rounded-xl border border-zinc-800/80 bg-black/30 p-4 shadow-inner shadow-black/30">
      <div className="mb-4 flex items-center justify-between gap-2">
        <button
          type="button"
          onClick={onPrev}
          className="rounded border border-zinc-700 px-3 py-1.5 text-xs font-medium text-zinc-300 hover:border-zinc-500 hover:text-white"
        >
          ← Mês
        </button>
        <p className="text-center text-sm font-semibold capitalize tracking-wide text-zinc-100">{title}</p>
        <button
          type="button"
          onClick={onNext}
          className="rounded border border-zinc-700 px-3 py-1.5 text-xs font-medium text-zinc-300 hover:border-zinc-500 hover:text-white"
        >
          Mês →
        </button>
      </div>
      <div className="grid grid-cols-7 gap-1 text-center text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
        {WEEK.map((w) => (
          <div key={w} className="py-1">
            {w}
          </div>
        ))}
      </div>
      <div className="mt-1 grid grid-cols-7 gap-1">
        {cells.map((c, idx) => {
          if (c.kind === "empty") {
            return <div key={`e-${idx}`} className="aspect-square rounded-md bg-transparent" />;
          }
          const day = byDate.get(c.iso);
          const statuses = new Set(day?.entries.map((e) => e.status) ?? []);
          const tone = day ? vacationStatusCellClass(statuses) : "bg-zinc-900/30 ring-1 ring-zinc-800/40";
          const sel = selected === c.iso;
          const baseCell = [
            "flex aspect-square flex-col items-center justify-center rounded-md text-sm font-medium transition",
            tone,
            sel ? "ring-2 ring-zinc-100 ring-offset-2 ring-offset-zinc-950" : "",
            "hover:brightness-110",
          ].join(" ");

          return (
            <button
              key={c.iso}
              type="button"
              onClick={() => onSelect(c.iso)}
              className={baseCell}
            >
              <span className="text-zinc-100">{c.n}</span>
              {day && day.is_critical && (
                <span className="mt-0.5 text-[8px] font-bold uppercase text-amber-400">crít.</span>
              )}
              {day && day.active_count > 0 && (
                <span className="text-[9px] text-zinc-500">{day.active_count} pol.</span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

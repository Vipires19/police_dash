import type { DejemShiftStatus } from "@/types/dejem";
import { DEJEM_SHIFT_STATUS_LABELS } from "@/types/dejem";

export function dejemShiftStatusLabel(status: DejemShiftStatus): string {
  return DEJEM_SHIFT_STATUS_LABELS[status];
}

export function dejemShiftStatusBadgeClass(status: DejemShiftStatus): string {
  if (status === "OPEN") return "bg-emerald-950/60 text-emerald-200 ring-1 ring-emerald-800/60";
  if (status === "CLOSED") return "bg-amber-950/50 text-amber-200 ring-1 ring-amber-800/50";
  if (status === "READY_FOR_MAP") return "bg-sky-950/50 text-sky-200 ring-1 ring-sky-800/50";
  if (status === "INTEGRATED") return "bg-violet-950/50 text-violet-200 ring-1 ring-violet-800/50";
  return "bg-zinc-800/80 text-zinc-300 ring-1 ring-zinc-700/60";
}

export function dejemShiftCalendarCellClass(day: {
  shift_count: number;
  has_open: boolean;
  has_closed: boolean;
  has_finished: boolean;
}): string {
  if (day.shift_count === 0) return "bg-zinc-900/30 ring-1 ring-zinc-800/40 text-zinc-500";
  if (day.has_open) return "bg-emerald-950/50 ring-1 ring-emerald-700/50 text-emerald-100";
  if (day.has_closed) return "bg-amber-950/40 ring-1 ring-amber-700/40 text-amber-100";
  return "bg-zinc-800/50 ring-1 ring-zinc-700/50 text-zinc-200";
}

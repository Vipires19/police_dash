import type { ScaleStatus } from "@/types/serviceScale";

export function scaleStatusLabel(status: ScaleStatus): string {
  return status === "PUBLISHED" ? "Publicada" : "Rascunho";
}

export function scaleStatusBadgeClass(status: ScaleStatus): string {
  return status === "PUBLISHED"
    ? "bg-emerald-950/60 text-emerald-300 ring-emerald-800/60"
    : "bg-amber-950/50 text-amber-200 ring-amber-800/50";
}

export function scaleCalendarCellClass(status: ScaleStatus | null | undefined): string {
  if (status === "PUBLISHED") {
    return "bg-emerald-950/50 ring-1 ring-emerald-700/50 text-emerald-100";
  }
  if (status === "DRAFT") {
    return "bg-amber-950/40 ring-1 ring-amber-700/40 text-amber-100";
  }
  return "bg-zinc-900/30 ring-1 ring-zinc-800/40 text-zinc-400";
}

export function absenceBadgeClass(kind: string): string {
  if (kind === "FOLGA") return "bg-sky-950/60 text-sky-300 ring-sky-800/50";
  if (kind === "FERIAS") return "bg-violet-950/60 text-violet-300 ring-violet-800/50";
  return "bg-orange-950/60 text-orange-300 ring-orange-800/50";
}

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
  const k = kind.toUpperCase();
  if (k === "FOLGA") return "bg-sky-950/60 text-sky-300 ring-sky-800/50";
  if (k === "DS") return "bg-cyan-950/60 text-cyan-300 ring-cyan-800/50";
  if (k === "FERIAS" || k === "FÉRIAS") return "bg-violet-950/60 text-violet-300 ring-violet-800/50";
  if (k === "LP") return "bg-orange-950/60 text-orange-300 ring-orange-800/50";
  if (k === "LICENCA" || k === "LICENÇA") return "bg-amber-950/60 text-amber-300 ring-amber-800/50";
  return "bg-zinc-900/60 text-zinc-400 ring-zinc-700/50";
}

/** Normaliza rótulo de ausência para badge operacional. */
export function absenceDisplayLabel(kind: string, label?: string): string {
  const raw = `${label ?? ""} ${kind}`.toUpperCase();
  if (/\bDS\b/.test(raw) || kind.toUpperCase() === "DS") return "DS";
  if (kind.toUpperCase() === "FERIAS" || raw.includes("FÉRIAS") || raw.includes("FERIAS")) return "FÉRIAS";
  if (kind.toUpperCase() === "LP" || /\bLP\b/.test(raw)) return "LP";
  if (raw.includes("LICEN")) return "LICENÇA";
  if (kind.toUpperCase() === "FOLGA" || raw.includes("FOLGA")) return "FOLGA";
  if (label?.trim()) return label.trim().toUpperCase();
  return "OUTROS";
}

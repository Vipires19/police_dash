import type { VacationStatus, VacationType } from "@/types/vacation";

export function vacationStatusLabel(s: VacationStatus): string {
  switch (s) {
    case "PENDING":
      return "Pendente";
    case "REVIEW":
      return "Revisão";
    case "APPROVED":
      return "Aprovada";
    case "REJECTED":
      return "Indeferida";
    case "CANCELLED":
      return "Cancelada";
    default:
      return s;
  }
}

export function vacationTypeLabel(t: VacationType): string {
  return t === "FERIAS" ? "Férias" : "LP";
}

export function vacationStatusCellClass(statuses: Set<VacationStatus>): string {
  if (statuses.has("REVIEW")) {
    return "ring-1 ring-amber-600/50 bg-amber-950/25";
  }
  if (statuses.has("PENDING")) {
    return "ring-1 ring-sky-700/50 bg-sky-950/25";
  }
  if (statuses.has("APPROVED")) {
    return "ring-1 ring-emerald-800/50 bg-emerald-950/20";
  }
  if (statuses.has("REJECTED")) {
    return "ring-1 ring-red-800/50 bg-red-950/20";
  }
  return "bg-zinc-900/40 ring-1 ring-zinc-800/60";
}

export function vacationStatusBadgeClass(s: VacationStatus): string {
  switch (s) {
    case "PENDING":
      return "border-sky-600/60 bg-sky-950/50 text-sky-200";
    case "REVIEW":
      return "border-amber-600/60 bg-amber-950/50 text-amber-100";
    case "APPROVED":
      return "border-emerald-700/60 bg-emerald-950/50 text-emerald-100";
    case "REJECTED":
      return "border-red-700/60 bg-red-950/50 text-red-100";
    case "CANCELLED":
      return "border-zinc-600/60 bg-zinc-900/60 text-zinc-400";
    default:
      return "border-zinc-700 bg-zinc-900 text-zinc-300";
  }
}

export function vacationTypeBadgeClass(t: VacationType): string {
  return t === "FERIAS"
    ? "border-violet-700/50 bg-violet-950/40 text-violet-200"
    : "border-cyan-700/50 bg-cyan-950/40 text-cyan-200";
}

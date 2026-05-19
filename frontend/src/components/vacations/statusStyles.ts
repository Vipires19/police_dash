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
    case "REVERTED":
      return "Revertida";
    default:
      return s;
  }
}

export function vacationTypeLabel(t: VacationType): string {
  switch (t) {
    case "FERIAS":
      return "Férias";
    case "LP":
      return "LP";
    case "LTS":
      return "LTS";
    case "CURSO":
      return "Curso";
    case "ESTAGIO_OPERACIONAL":
      return "Estágio operacional";
    case "OUTROS":
      return "Outros";
    default:
      return t;
  }
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
    case "REVERTED":
      return "border-violet-700/60 bg-violet-950/50 text-violet-200";
    default:
      return "border-zinc-700 bg-zinc-900 text-zinc-300";
  }
}

export function vacationTypeBadgeClass(t: VacationType): string {
  switch (t) {
    case "FERIAS":
      return "border-violet-700/50 bg-violet-950/40 text-violet-200";
    case "LP":
      return "border-cyan-700/50 bg-cyan-950/40 text-cyan-200";
    case "LTS":
      return "border-orange-700/50 bg-orange-950/40 text-orange-200";
    case "CURSO":
      return "border-blue-700/50 bg-blue-950/40 text-blue-200";
    case "ESTAGIO_OPERACIONAL":
      return "border-teal-700/50 bg-teal-950/40 text-teal-200";
    case "OUTROS":
      return "border-zinc-600/50 bg-zinc-900/60 text-zinc-300";
    default:
      return "border-zinc-700 bg-zinc-900 text-zinc-300";
  }
}

export function vacationTypeDotClass(t: VacationType): string {
  switch (t) {
    case "FERIAS":
      return "bg-violet-400";
    case "LP":
      return "bg-cyan-400";
    case "LTS":
      return "bg-orange-400";
    case "CURSO":
      return "bg-blue-400";
    case "ESTAGIO_OPERACIONAL":
      return "bg-teal-400";
    case "OUTROS":
      return "bg-zinc-400";
    default:
      return "bg-zinc-500";
  }
}

export const ABSENCE_LEGEND: { type: VacationType; label: string }[] = [
  { type: "FERIAS", label: "Férias" },
  { type: "LP", label: "LP" },
  { type: "LTS", label: "LTS" },
  { type: "CURSO", label: "Curso" },
  { type: "ESTAGIO_OPERACIONAL", label: "Estágio op." },
  { type: "OUTROS", label: "Outros" },
];

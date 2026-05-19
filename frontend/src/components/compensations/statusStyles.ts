import type { CompensationEventStatus } from "@/types/compensations";

export function compensationStatusLabel(status: CompensationEventStatus): string {
  const map: Record<CompensationEventStatus, string> = {
    PENDING: "Pendente",
    APPROVED: "Aprovado",
    REJECTED: "Indeferido",
    CANCELLED: "Cancelado",
    REVERTED: "Revertido",
  };
  return map[status];
}

export function compensationStatusBadgeClass(status: CompensationEventStatus): string {
  switch (status) {
    case "APPROVED":
      return "border-emerald-800/60 bg-emerald-950/40 text-emerald-200";
    case "PENDING":
      return "border-amber-800/60 bg-amber-950/40 text-amber-200";
    case "REJECTED":
      return "border-red-800/60 bg-red-950/40 text-red-200";
    case "CANCELLED":
      return "border-zinc-600/60 bg-zinc-900/60 text-zinc-400";
    case "REVERTED":
      return "border-violet-800/60 bg-violet-950/40 text-violet-200";
    default:
      return "border-zinc-700 text-zinc-400";
  }
}

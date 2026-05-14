import type { VehicleStatus } from "@/types/vehicle";

const map: Record<
  VehicleStatus,
  { label: string; className: string }
> = {
  OPERANDO: {
    label: "OPERANDO",
    className: "border-emerald-900/50 bg-emerald-950/40 text-emerald-200",
  },
  BAIXADA: {
    label: "BAIXADA",
    className: "border-red-900/50 bg-red-950/40 text-red-200",
  },
  MANUTENCAO: {
    label: "MANUTENÇÃO",
    className: "border-amber-900/50 bg-amber-950/35 text-amber-200",
  },
  RESERVA: {
    label: "RESERVA",
    className: "border-zinc-700 bg-zinc-900/80 text-zinc-300",
  },
};

export function VehicleStatusBadge({ status }: { status: VehicleStatus }) {
  const cfg = map[status];
  return (
    <span
      className={[
        "inline-flex rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
        cfg.className,
      ].join(" ")}
    >
      {cfg.label}
    </span>
  );
}

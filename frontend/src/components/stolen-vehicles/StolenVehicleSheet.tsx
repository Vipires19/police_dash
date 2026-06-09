import type { StolenVehicleSheetGroup, StolenVehicleSheetResponse } from "@/types/stolenVehicles";
import { SheetGroupTable } from "./SheetGroupTable";

function SheetSection({ title, groups }: { title: string; groups: StolenVehicleSheetGroup[] }) {
  return (
    <section className="space-y-3">
      <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-zinc-400">{title}</h3>
      <div className="grid grid-cols-2 gap-3">
        {groups.map((g) => (
          <SheetGroupTable key={`${title}-${g.group}`} group={g} variant="screen" />
        ))}
      </div>
    </section>
  );
}

interface Props {
  sheet: StolenVehicleSheetResponse;
  onPrint: () => void;
}

export function StolenVehicleSheet({ sheet, onPrint }: Props) {
  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-zinc-500">
          Folha 0 a 9 — tabela contínua por grupo (0|1, 2|3…). Preenchimento de baixo para cima; apenas veículos não
          localizados.
        </p>
        <button
          type="button"
          onClick={onPrint}
          className="rounded-lg border border-zinc-600 bg-zinc-100 px-4 py-2 text-sm font-semibold text-zinc-900 hover:bg-white"
        >
          Imprimir Folha
        </button>
      </div>

      <SheetSection title="Carros" groups={sheet.carros} />
      <SheetSection title="Motos" groups={sheet.motos} />
    </div>
  );
}

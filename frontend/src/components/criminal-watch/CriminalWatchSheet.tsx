import type { CriminalWatchSheetResponse } from "@/types/criminalWatch";
import { CriminalWatchSheetTable } from "./CriminalWatchSheetTable";

interface Props {
  sheet: CriminalWatchSheetResponse;
  onPrint: () => void;
}

export function CriminalWatchSheet({ sheet, onPrint }: Props) {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-zinc-500">
          Folha operacional C05 — 15 registros mais recentes. Preenchimento de baixo para cima; histórico completo
          permanece no banco.
        </p>
        <button
          type="button"
          onClick={onPrint}
          className="rounded-lg border border-zinc-600 bg-zinc-100 px-4 py-2 text-sm font-semibold text-zinc-900 hover:bg-white"
        >
          Imprimir Folha
        </button>
      </div>

      <div className="overflow-x-auto rounded-xl border border-zinc-800/80 p-2">
        <CriminalWatchSheetTable slots={sheet.slots} variant="screen" />
      </div>
    </div>
  );
}

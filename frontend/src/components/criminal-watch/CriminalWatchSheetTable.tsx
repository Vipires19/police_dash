import type { CriminalWatchSheetEntry } from "@/types/criminalWatch";

interface Props {
  slots: CriminalWatchSheetEntry[];
  variant: "screen" | "print";
}

export function CriminalWatchSheetTable({ slots, variant }: Props) {
  const isPrint = variant === "print";

  return (
    <div className={isPrint ? "c05-sheet-wrap" : ""}>
      <table className={isPrint ? "c05-sheet-table" : "w-full border-collapse text-sm"}>
        <thead>
          <tr className={isPrint ? "" : "border-b border-zinc-800"}>
            <th className={isPrint ? "col-numeric" : "px-2 py-2 text-left text-xs uppercase text-zinc-500"}>
              Placa (nº)
            </th>
            <th className={isPrint ? "col-letters" : "px-2 py-2 text-left text-xs uppercase text-zinc-500"}>
              Letras
            </th>
            <th className={isPrint ? "col-model" : "px-2 py-2 text-left text-xs uppercase text-zinc-500"}>
              Modelo
            </th>
            <th className={isPrint ? "col-color" : "px-2 py-2 text-left text-xs uppercase text-zinc-500"}>Cor</th>
            <th className={isPrint ? "col-year" : "px-2 py-2 text-left text-xs uppercase text-zinc-500"}>Ano</th>
            <th className={isPrint ? "col-qru" : "px-2 py-2 text-left text-xs uppercase text-zinc-500"}>QRU</th>
          </tr>
        </thead>
        <tbody>
          {slots.map((slot, idx) => (
            <tr
              key={slot.id ?? `empty-${idx}`}
              className={isPrint ? "" : "border-b border-zinc-800/60 hover:bg-zinc-900/30"}
            >
              <td className={isPrint ? "col-numeric" : "px-2 py-1.5 font-mono text-zinc-300"}>
                {slot.plate_numeric ?? ""}
              </td>
              <td className={isPrint ? "col-letters" : "px-2 py-1.5 font-mono text-zinc-300"}>
                {slot.plate_letters ?? ""}
              </td>
              <td className={isPrint ? "col-model" : "px-2 py-1.5 text-zinc-200"}>{slot.vehicle_model ?? ""}</td>
              <td className={isPrint ? "col-color" : "px-2 py-1.5 text-zinc-400"}>{slot.color_abbr ?? ""}</td>
              <td className={isPrint ? "col-year" : "px-2 py-1.5 text-zinc-400"}>{slot.year_short ?? ""}</td>
              <td className={isPrint ? "col-qru" : "px-2 py-1.5 font-mono text-zinc-400"}>{slot.qru_code ?? ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

import type { StolenVehicleSheetGroup } from "@/types/stolenVehicles";
import { buildPlateCells, isGroupOnLeftMargin, slotFrLabel } from "./sheetGroupTableUtils";

type Variant = "print" | "screen";

interface Props {
  group: StolenVehicleSheetGroup;
  variant: Variant;
}

function PlateCells({ plate, groupNum, variant }: { plate: string | null | undefined; groupNum: number; variant: Variant }) {
  const cells = buildPlateCells(plate, groupNum);
  const cellClass = variant === "print" ? "sheet-plate-cell" : "flex flex-1 items-center justify-center border-r border-zinc-600/80 text-[10px] font-bold last:border-r-0";

  return (
    <div className={variant === "print" ? "sheet-plate-cells" : "flex h-full min-h-[1.25rem]"}>
      {cells.map((ch, i) => (
        <span key={i} className={cellClass}>
          {ch}
        </span>
      ))}
    </div>
  );
}

export function SheetGroupTable({ group, variant }: Props) {
  const onLeft = isGroupOnLeftMargin(group.group);

  const wrapClass =
    variant === "print"
      ? `sheet-group-wrap ${onLeft ? "sheet-group-wrap--left" : "sheet-group-wrap--right"}`
      : `flex min-h-0 items-stretch ${onLeft ? "flex-row" : "flex-row-reverse"}`;

  const digitClass =
    variant === "print"
      ? "sheet-group-digit"
      : "flex shrink-0 items-center px-1 text-2xl font-bold leading-none text-zinc-300";

  const tableClass =
    variant === "print" ? "sheet-group-table" : "w-full table-fixed border-collapse text-[10px] text-zinc-200";

  const thClass =
    variant === "print"
      ? undefined
      : "border border-zinc-600/80 bg-zinc-900/60 px-0.5 py-0.5 text-center text-[9px] font-semibold uppercase text-zinc-400";

  const tdClass = variant === "print" ? undefined : "border border-zinc-600/80 px-1 py-0.5 align-middle";

  return (
    <div className={wrapClass}>
      <span className={digitClass} aria-hidden>
        {group.group}
      </span>
      <div className={variant === "print" ? "sheet-group-table-wrap" : "min-w-0 flex-1"}>
        <table className={tableClass}>
          <thead>
            <tr>
              <th className={[thClass ?? "col-placa", variant === "screen" ? "w-[30%]" : ""].filter(Boolean).join(" ")}>
                Placa
              </th>
              <th className={[thClass ?? "col-veiculo", variant === "screen" ? "w-[40%]" : ""].filter(Boolean).join(" ")}>
                Veículo
              </th>
              <th className={[thClass ?? "col-cor", variant === "screen" ? "w-[15%]" : ""].filter(Boolean).join(" ")}>
                Cor
              </th>
              <th className={[thClass ?? "col-ano", variant === "screen" ? "w-[10%]" : ""].filter(Boolean).join(" ")}>
                Ano
              </th>
              <th className={[thClass ?? "col-fr", variant === "screen" ? "w-[5%]" : ""].filter(Boolean).join(" ")}>
                F/R
              </th>
            </tr>
          </thead>
          <tbody>
            {group.slots.map((slot, idx) => (
              <tr key={idx} className={variant === "screen" ? "h-7" : undefined}>
                <td className={tdClass ?? "col-placa"}>
                  <PlateCells plate={slot.plate} groupNum={group.group} variant={variant} />
                </td>
                <td className={tdClass ?? "col-veiculo"}>{slot.vehicle_model ?? ""}</td>
                <td className={tdClass ?? "col-cor"}>{slot.color ?? ""}</td>
                <td className={[tdClass ?? "col-ano", variant === "screen" ? "text-center" : ""].filter(Boolean).join(" ")}>
                  {slot.year ?? ""}
                </td>
                <td className={[tdClass ?? "col-fr", variant === "screen" ? "text-center font-bold" : ""].filter(Boolean).join(" ")}>
                  {slotFrLabel(slot)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

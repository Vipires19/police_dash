import type { StolenVehicleSheetGroup, StolenVehicleSheetResponse } from "@/types/stolenVehicles";
import { SheetGroupTable } from "./SheetGroupTable";

const ESCUDO_SRC = "/images/escudo_pelotao.png";

function PrintGroupsGrid({ groups }: { groups: StolenVehicleSheetGroup[] }) {
  return (
    <div className="print-groups">
      {groups.map((group) => (
        <SheetGroupTable key={group.group} group={group} variant="print" />
      ))}
    </div>
  );
}

function PrintPageHeader({ subtitle }: { subtitle: string }) {
  return (
    <header className="print-brand-header">
      <div className="print-brand-row">
        <img src={ESCUDO_SRC} alt="" className="print-escudo" />
        <div className="print-brand-text">
          <h1 className="print-title-main">CARATER GERAL</h1>
          <h2 className="print-title-sub">{subtitle}</h2>
        </div>
        <img src={ESCUDO_SRC} alt="" className="print-escudo" />
      </div>
    </header>
  );
}

interface Props {
  sheet: StolenVehicleSheetResponse;
}

export function StolenVehiclePrint({ sheet }: Props) {
  return (
    <div id="stolen-vehicle-print-root" className="hidden print:block">
      <style>{`
        @media print {
          @page {
            size: A4 portrait;
            margin: 5mm;
          }

          html,
          body {
            margin: 0 !important;
            padding: 0 !important;
            background: #fff !important;
          }

          body * {
            visibility: hidden !important;
          }

          #stolen-vehicle-print-root,
          #stolen-vehicle-print-root * {
            visibility: visible !important;
          }

          #stolen-vehicle-print-root {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            color: #000;
            background: #fff;
            font-family: "Times New Roman", Times, serif;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
          }

          .print-page {
            display: flex;
            flex-direction: column;
            height: 287mm;
            max-height: 287mm;
            page-break-after: always;
            break-after: page;
            page-break-inside: avoid;
            break-inside: avoid;
            overflow: hidden;
          }

          .print-page:last-child {
            page-break-after: auto;
            break-after: auto;
          }

          .print-brand-header {
            flex-shrink: 0;
            margin-bottom: 2mm;
            padding-bottom: 1.5mm;
          }

          .print-brand-row {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 4mm;
          }

          .print-escudo {
            width: 13mm;
            height: 13mm;
            object-fit: contain;
            flex-shrink: 0;
          }

          .print-brand-text {
            text-align: center;
          }

          .print-title-main {
            margin: 0;
            font-size: 14pt;
            font-weight: bold;
            letter-spacing: 0.08em;
            line-height: 1.1;
            text-transform: uppercase;
          }

          .print-title-sub {
            margin: 1mm 0 0;
            font-size: 10pt;
            font-weight: bold;
            letter-spacing: 0.15em;
            line-height: 1.1;
            text-transform: uppercase;
          }

          /* 0|1, 2|3, 4|5, 6|7, 8|9 */
          .print-groups {
            flex: 1;
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: repeat(5, 1fr);
            gap: 1.5mm 2mm;
            min-height: 0;
          }

          .sheet-group-wrap {
            display: flex;
            align-items: stretch;
            min-height: 0;
            overflow: hidden;
            page-break-inside: avoid;
            break-inside: avoid;
          }

          .sheet-group-wrap--left {
            flex-direction: row;
          }

          .sheet-group-wrap--right {
            flex-direction: row-reverse;
          }

          .sheet-group-digit {
            flex-shrink: 0;
            width: 5mm;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16pt;
            font-weight: bold;
            line-height: 1;
            padding: 0 0.5mm;
          }

          .sheet-group-table-wrap {
            flex: 1;
            min-width: 0;
            min-height: 0;
            display: flex;
            flex-direction: column;
          }

          .sheet-group-table {
            width: 100%;
            height: 100%;
            border-collapse: collapse;
            table-layout: fixed;
            border: 1pt solid #000;
          }

          .sheet-group-table th,
          .sheet-group-table td {
            border: 1pt solid #000;
            padding: 0;
            vertical-align: middle;
            overflow: hidden;
            color: #000;
          }

          .sheet-group-table thead th {
            font-size: 5.5pt;
            font-weight: bold;
            text-align: center;
            padding: 0.3mm 0;
            line-height: 1;
            height: 4mm;
          }

          .sheet-group-table tbody td {
            font-size: 6pt;
            line-height: 1.1;
            height: calc((100% - 4mm) / 10);
            padding: 0 0.5mm;
          }

          .col-placa { width: 30%; }
          .col-veiculo { width: 40%; }
          .col-cor { width: 15%; }
          .col-ano { width: 10%; text-align: center; }
          .col-fr { width: 5%; text-align: center; font-weight: bold; }

          .sheet-group-table tbody td.col-veiculo,
          .sheet-group-table tbody td.col-cor {
            font-size: 7.5pt;
            font-weight: 600;
            text-align: center;
            vertical-align: middle;
            text-transform: uppercase;
            letter-spacing: 0.02em;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            padding: 0 0.8mm;
          }

          .sheet-plate-cells {
            display: flex;
            height: 100%;
            width: 100%;
          }

          .sheet-plate-cell {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            border-right: 1pt solid #000;
            font-size: 5.5pt;
            font-weight: bold;
            min-width: 0;
            height: 100%;
          }

          .sheet-plate-cell:last-child {
            border-right: none;
          }
        }
      `}</style>

      <div className="print-page">
        <PrintPageHeader subtitle="CARROS" />
        <PrintGroupsGrid groups={sheet.carros} />
      </div>

      <div className="print-page">
        <PrintPageHeader subtitle="MOTOS" />
        <PrintGroupsGrid groups={sheet.motos} />
      </div>
    </div>
  );
}

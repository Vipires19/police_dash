import type { CriminalWatchSheetResponse } from "@/types/criminalWatch";
import { CriminalWatchSheetTable } from "./CriminalWatchSheetTable";

const ESCUDO_SRC = "/images/escudo_pelotao.png";

interface Props {
  sheet: CriminalWatchSheetResponse;
}

export function CriminalWatchPrint({ sheet }: Props) {
  return (
    <div id="criminal-watch-print-root" className="hidden print:block">
      <style>{`
        @media print {
          @page {
            size: A4 portrait;
            margin: 4mm;
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

          #criminal-watch-print-root,
          #criminal-watch-print-root * {
            visibility: visible !important;
          }

          #criminal-watch-print-root {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            height: 289mm;
            max-height: 289mm;
            display: flex;
            flex-direction: column;
            box-sizing: border-box;
            color: #000;
            background: #fff;
            font-family: "Arial", "Helvetica Neue", Helvetica, sans-serif;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
            overflow: hidden;
          }

          .c05-print-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;
            flex-shrink: 0;
            height: 16mm;
            margin-bottom: 1.5mm;
            padding: 0;
          }

          .c05-print-escudo {
            width: 20mm;
            height: 20mm;
            object-fit: contain;
            flex-shrink: 0;
          }

          .c05-print-title {
            flex: 1;
            text-align: center;
            padding: 0 3mm;
          }

          .c05-print-title h1 {
            margin: 0;
            font-size: 13pt;
            font-weight: 700;
            letter-spacing: 0.08em;
            line-height: 1.1;
            text-transform: uppercase;
          }

          .c05-print-title h2 {
            margin: 0.5mm 0 0;
            font-size: 10pt;
            font-weight: 700;
            letter-spacing: 0.12em;
            line-height: 1.1;
            text-transform: uppercase;
          }

          .c05-sheet-wrap {
            flex: 1;
            min-height: 0;
            display: flex;
            flex-direction: column;
          }

          .c05-sheet-table {
            width: 100%;
            height: 100%;
            border-collapse: collapse;
            table-layout: fixed;
            border: 1.2pt solid #000;
          }

          .c05-sheet-table th,
          .c05-sheet-table td {
            border: 1pt solid #000;
            vertical-align: middle;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            color: #000;
            text-transform: uppercase;
          }

          .c05-sheet-table thead th {
            font-size: 8.5pt;
            font-weight: 700;
            text-align: center;
            height: 5.5mm;
            line-height: 1;
            padding: 0.5mm 0.6mm;
          }

          .c05-sheet-table tbody td {
            height: calc((271.5mm - 5.5mm) / 15);
            max-height: calc((271.5mm - 5.5mm) / 15);
            padding: 0.15mm 0.4mm;
            font-size: 14pt;
            font-weight: 700;
            text-align: center;
            line-height: 1;
            letter-spacing: 0.02em;
          }

          .col-numeric { width: 15%; }
          .col-letters { width: 9%; }
          .col-model { width: 28%; }
          .col-color { width: 18%; }
          .col-year { width: 7%; }
          .col-qru { width: 10%; }
        }
      `}</style>

      <header className="c05-print-header">
        <img src={ESCUDO_SRC} alt="" className="c05-print-escudo" />
        <div className="c05-print-title">
          <h1>Veículos C05</h1>
          <h2>Monitoramento Operacional</h2>
        </div>
        <img src={ESCUDO_SRC} alt="" className="c05-print-escudo" />
      </header>

      <CriminalWatchSheetTable slots={sheet.slots} variant="print" />
    </div>
  );
}

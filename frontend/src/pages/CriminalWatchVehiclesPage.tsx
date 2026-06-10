import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { CriminalWatchForm } from "@/components/criminal-watch/CriminalWatchForm";
import { CriminalWatchPrint } from "@/components/criminal-watch/CriminalWatchPrint";
import { CriminalWatchSearch } from "@/components/criminal-watch/CriminalWatchSearch";
import { CriminalWatchSheet } from "@/components/criminal-watch/CriminalWatchSheet";
import { QruCodeAdmin } from "@/components/criminal-watch/QruCodeAdmin";
import { OperationalLayout } from "@/layouts/OperationalLayout";
import { useAuth } from "@/hooks/AuthContext";
import { ApiError } from "@/services/api";
import * as criminalWatchApi from "@/services/criminalWatchApi";
import type { CriminalWatchSheetResponse } from "@/types/criminalWatch";

type TabId = "cadastro" | "folha" | "consulta" | "qru";

const TABS: { id: TabId; label: string }[] = [
  { id: "cadastro", label: "Cadastro" },
  { id: "folha", label: "Folha" },
  { id: "consulta", label: "Consulta" },
  { id: "qru", label: "QRUs" },
];

export function CriminalWatchVehiclesPage() {
  const { token } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const activeTab: TabId = useMemo(() => {
    const raw = searchParams.get("tab");
    return raw && TABS.some((t) => t.id === raw) ? (raw as TabId) : "cadastro";
  }, [searchParams]);

  const setTab = (id: TabId) => {
    setSearchParams({ tab: id }, { replace: true });
  };

  const [sheet, setSheet] = useState<CriminalWatchSheetResponse | null>(null);
  const [sheetLoading, setSheetLoading] = useState(false);
  const [sheetError, setSheetError] = useState<string | null>(null);

  const loadSheet = useCallback(async () => {
    if (!token) return;
    setSheetLoading(true);
    setSheetError(null);
    try {
      const data = await criminalWatchApi.getCriminalWatchSheet(token);
      setSheet(data);
    } catch (e) {
      setSheetError(e instanceof ApiError ? e.detail : "Erro ao carregar folha");
    } finally {
      setSheetLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (activeTab === "folha" || activeTab === "cadastro") {
      void loadSheet();
    }
  }, [activeTab, loadSheet]);

  const handlePrint = () => {
    window.print();
  };

  return (
    <OperationalLayout>
      <CriminalWatchPrint sheet={sheet ?? { slots: [] }} />

      <header className="mb-6">
        <p className="text-xs uppercase tracking-[0.35em] text-zinc-500">Operacional</p>
        <h2 className="text-2xl font-semibold text-zinc-50">Veículos C05</h2>
        <p className="mt-2 max-w-3xl text-sm text-zinc-400">
          Monitoramento de veículos de interesse policial — denúncias, atitudes suspeitas e ocorrências operacionais.
          A folha exibe os 15 mais recentes; o histórico completo permanece no banco.
        </p>
      </header>

      <nav className="mb-8 flex flex-wrap gap-2 border-b border-zinc-800/80 pb-4">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={[
              "rounded-lg border px-4 py-2 text-xs font-semibold uppercase tracking-wide transition",
              activeTab === t.id
                ? "border-zinc-500 bg-zinc-900/80 text-zinc-50"
                : "border-zinc-800/80 bg-black/30 text-zinc-500 hover:border-zinc-600 hover:text-zinc-200",
            ].join(" ")}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {activeTab === "cadastro" && token && (
        <CriminalWatchForm token={token} onCreated={() => void loadSheet()} />
      )}

      {activeTab === "folha" && (
        <>
          {sheetLoading && <p className="text-sm text-zinc-500">Carregando folha…</p>}
          {sheetError && (
            <p className="rounded-lg border border-red-900/60 bg-red-950/40 px-4 py-3 text-sm text-red-300">
              {sheetError}
            </p>
          )}
          {sheet && !sheetLoading && <CriminalWatchSheet sheet={sheet} onPrint={handlePrint} />}
        </>
      )}

      {activeTab === "consulta" && token && (
        <CriminalWatchSearch token={token} onDataChanged={() => void loadSheet()} />
      )}

      {activeTab === "qru" && token && <QruCodeAdmin token={token} />}
    </OperationalLayout>
  );
}

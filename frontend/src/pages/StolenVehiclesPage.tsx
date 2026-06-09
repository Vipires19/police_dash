import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { StolenVehicleForm } from "@/components/stolen-vehicles/StolenVehicleForm";
import { StolenVehiclePrint } from "@/components/stolen-vehicles/StolenVehiclePrint";
import { StolenVehicleSearch } from "@/components/stolen-vehicles/StolenVehicleSearch";
import { StolenVehicleSheet } from "@/components/stolen-vehicles/StolenVehicleSheet";
import { OperationalLayout } from "@/layouts/OperationalLayout";
import { useAuth } from "@/hooks/AuthContext";
import { ApiError } from "@/services/api";
import * as stolenVehiclesApi from "@/services/stolenVehiclesApi";
import type { StolenVehicleSheetResponse } from "@/types/stolenVehicles";

type TabId = "cadastro" | "folha" | "consulta";

const TABS: { id: TabId; label: string }[] = [
  { id: "cadastro", label: "Cadastro" },
  { id: "folha", label: "Folha 0 a 9" },
  { id: "consulta", label: "Consulta" },
];

export function StolenVehiclesPage() {
  const { token } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const activeTab: TabId = useMemo(() => {
    const raw = searchParams.get("tab");
    return raw && TABS.some((t) => t.id === raw) ? (raw as TabId) : "cadastro";
  }, [searchParams]);

  const setTab = (id: TabId) => {
    setSearchParams({ tab: id }, { replace: true });
  };

  const [sheet, setSheet] = useState<StolenVehicleSheetResponse | null>(null);
  const [sheetLoading, setSheetLoading] = useState(false);
  const [sheetError, setSheetError] = useState<string | null>(null);

  const loadSheet = useCallback(async () => {
    if (!token) return;
    setSheetLoading(true);
    setSheetError(null);
    try {
      const data = await stolenVehiclesApi.getStolenVehicleSheet(token);
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
      <StolenVehiclePrint sheet={sheet ?? { carros: [], motos: [] }} />

      <header className="mb-6">
        <p className="text-xs uppercase tracking-[0.35em] text-zinc-500">Operacional</p>
        <h2 className="text-2xl font-semibold text-zinc-50">Veículos Produtos de Crime</h2>
        <p className="mt-2 max-w-3xl text-sm text-zinc-400">
          Controle digital da folha &quot;0 a 9&quot; para acompanhamento de veículos produtos de furto e roubo. O
          histórico completo permanece no banco; a folha exibe apenas os 10 mais recentes por grupo, não localizados.
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
        <StolenVehicleForm token={token} onCreated={() => void loadSheet()} />
      )}

      {activeTab === "folha" && (
        <>
          {sheetLoading && <p className="text-sm text-zinc-500">Carregando folha…</p>}
          {sheetError && (
            <p className="rounded-lg border border-red-900/60 bg-red-950/40 px-4 py-3 text-sm text-red-300">
              {sheetError}
            </p>
          )}
          {sheet && !sheetLoading && <StolenVehicleSheet sheet={sheet} onPrint={handlePrint} />}
        </>
      )}

      {activeTab === "consulta" && token && (
        <StolenVehicleSearch token={token} onRecovered={() => void loadSheet()} />
      )}
    </OperationalLayout>
  );
}

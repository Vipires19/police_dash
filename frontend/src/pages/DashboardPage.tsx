import { useCallback, useEffect, useState } from "react";
import { OperationalLayout } from "@/layouts/OperationalLayout";
import { useAuth } from "@/hooks/AuthContext";
import type { VehicleLogFeedItem } from "@/types/vehicle";
import { ApiError } from "@/services/api";
import * as vehiclesApi from "@/services/vehiclesApi";

function feedGlyph(log: VehicleLogFeedItem): string {
  if (log.action_type === "CREATED" || log.action_type === "RETURNED") return "🟢";
  if (log.new_status === "BAIXADA") return "🔴";
  if (log.new_status === "MANUTENCAO") return "🟡";
  if (log.new_status === "RESERVA") return "⚪";
  return "🔵";
}

export function DashboardPage() {
  const { user, token } = useAuth();
  const [feed, setFeed] = useState<VehicleLogFeedItem[]>([]);
  const [feedErr, setFeedErr] = useState<string | null>(null);

  const loadFeed = useCallback(async () => {
    if (!token) return;
    try {
      const rows = await vehiclesApi.listRecentVehicleLogs(token, 12);
      setFeed(rows);
      setFeedErr(null);
    } catch (e) {
      setFeedErr(e instanceof ApiError ? e.detail : "Logs indisponíveis");
    }
  }, [token]);

  useEffect(() => {
    void loadFeed();
  }, [loadFeed]);

  return (
    <OperationalLayout>
      <section className="rounded-xl border border-zinc-800 bg-zinc-950/70 p-8 shadow-inner shadow-black/40">
        <p className="text-xs uppercase tracking-[0.4em] text-zinc-500">Painel inicial</p>
        <h2 className="mt-3 text-3xl font-semibold text-zinc-50">1° Pel Força Tática/ROCAM</h2>
        {user && (
          <p className="mt-6 text-xl text-zinc-200">
            Bem-vindo {user.patente} {user.nome_guerra}
          </p>
        )}
        <div className="mt-8 grid gap-4 border-t border-zinc-800/80 pt-6 text-sm text-zinc-400 sm:grid-cols-2">
          <div className="rounded-lg border border-zinc-800/80 bg-black/30 p-4">
            <p className="text-xs uppercase tracking-wide text-zinc-500">Status operacional</p>
            <p className="mt-2 text-zinc-200">Base pronta para expansão (escalas, DEJEM, ROCAM).</p>
          </div>
          <div className="rounded-lg border border-zinc-800/80 bg-black/30 p-4">
            <p className="text-xs uppercase tracking-wide text-zinc-500">Próximos módulos</p>
            <p className="mt-2 text-zinc-200">Controle operacional, integrações e IA serão plugados aqui.</p>
          </div>
        </div>
      </section>

      <section className="mt-8 rounded-xl border border-zinc-800 bg-zinc-950/60 p-6 shadow-inner shadow-black/30">
        <p className="text-xs uppercase tracking-[0.35em] text-zinc-500">Viaturas</p>
        <h3 className="mt-2 text-lg font-semibold text-zinc-100">Últimos registros operacionais</h3>
        {feedErr && <p className="mt-3 text-sm text-red-400">{feedErr}</p>}
        {!feedErr && feed.length === 0 && (
          <p className="mt-4 text-sm text-zinc-500">Nenhum log registrado ainda.</p>
        )}
        <ul className="mt-4 divide-y divide-zinc-800/80">
          {feed.map((log) => (
            <li key={log.id} className="flex gap-3 py-3 first:pt-0">
              <span className="shrink-0 pt-0.5 text-base leading-none">{feedGlyph(log)}</span>
              <div className="min-w-0">
                <p className="text-sm text-zinc-200">
                  <span className="font-mono text-zinc-400">{log.vehicle_prefixo}</span> — {log.description}
                </p>
                <p className="mt-1 text-[11px] text-zinc-500">
                  {new Date(log.created_at).toLocaleString("pt-BR")} · {log.actor_label}
                </p>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </OperationalLayout>
  );
}

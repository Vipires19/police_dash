import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { leaveStatusBadgeClass, leaveStatusLabel } from "@/components/folgas/statusStyles";
import { leaveTypeLabel } from "@/components/folgas/leaveTypeLabels";
import {
  vacationStatusBadgeClass,
  vacationStatusLabel,
  vacationTypeLabel,
} from "@/components/vacations/statusStyles";
import { OrgUnitBadge, orgBadgeVariantForViewer } from "@/components/OrgUnitBadge";
import { OperationalLayout } from "@/layouts/OperationalLayout";
import { useAuth } from "@/hooks/AuthContext";
import type { OrganizationalUnit, Role, User } from "@/types";
import {
  ALL_ROLES,
  ORGANIZATIONAL_UNITS,
  ORGANIZATIONAL_UNIT_LABELS,
} from "@/types";
import type { LeaveRequestPublic } from "@/types/leaves";
import type { CompensationEventPublic } from "@/types/compensations";
import { COMPENSATION_TYPE_LABELS } from "@/types/compensations";
import type { VacationRequestPublic } from "@/types/vacation";
import { ApiError } from "@/services/api";
import * as authApi from "@/services/authApi";
import * as compensationsApi from "@/services/compensationsApi";
import * as leavesApi from "@/services/leavesApi";
import * as absencesApi from "@/services/absencesApi";
import * as usersApi from "@/services/usersApi";

const ROLES: Role[] = ALL_ROLES;
const UNITS: OrganizationalUnit[] = ORGANIZATIONAL_UNITS;

type TabId = "cadastros" | "folgas" | "afastamentos" | "compensacoes";

export function PendingUsersPage() {
  const { token, refreshUser, isApprover, user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const tabOptions = useMemo(() => {
    const o: { id: TabId; label: string }[] = [];
    if (isApprover) {
      o.push({ id: "cadastros", label: "Cadastros pendentes" });
      o.push({ id: "folgas", label: "Folgas pendentes" });
      o.push({ id: "afastamentos", label: "Afastamentos pendentes" });
    }
    if (isApprover) {
      o.push({ id: "compensacoes", label: "Compensações pendentes" });
    }
    return o;
  }, [isApprover]);

  const defaultTab: TabId = "cadastros";

  const rawTab = searchParams.get("tab");
  const normalizedTab = rawTab === "ferias" ? "afastamentos" : rawTab;
  const activeTab: TabId = useMemo(() => {
    const t =
      normalizedTab && tabOptions.some((x) => x.id === normalizedTab)
        ? (normalizedTab as TabId)
        : defaultTab;
    return t;
  }, [rawTab, tabOptions, defaultTab]);

  useEffect(() => {
    if (!rawTab || !tabOptions.some((x) => x.id === rawTab)) {
      setSearchParams({ tab: activeTab }, { replace: true });
    }
  }, [rawTab, tabOptions, activeTab, setSearchParams]);

  const setTab = (id: TabId) => {
    setSearchParams({ tab: id }, { replace: true });
  };

  return (
    <OperationalLayout>
      <header className="mb-6">
        <p className="text-xs uppercase tracking-[0.35em] text-zinc-500">Comando</p>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <h2 className="text-2xl font-semibold text-zinc-50">Central de aprovações</h2>
          {user && <OrgUnitBadge variant={orgBadgeVariantForViewer(user)} />}
        </div>
        <p className="mt-2 max-w-3xl text-sm text-zinc-400">
          Fila unificada: cadastros, folgas e eventos de compensação. Decisões permanecem manuais; o sistema apenas
          sinaliza revisões automáticas quando aplicável.
        </p>
      </header>

      <nav className="mb-8 flex flex-wrap gap-2 border-b border-zinc-800/80 pb-4">
        {tabOptions.map((t) => (
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

      {activeTab === "cadastros" && isApprover && <CadastrosPendentesSection token={token} refreshUser={refreshUser} />}
      {activeTab === "folgas" && isApprover && <FolgasPendentesSection token={token} />}
      {activeTab === "afastamentos" && isApprover && <AfastamentosPendentesSection token={token} />}
      {activeTab === "compensacoes" && isApprover && <CompensacoesApprovalSection token={token} />}
    </OperationalLayout>
  );
}

function CadastrosPendentesSection({
  token,
  refreshUser,
}: {
  token: string | null;
  refreshUser: () => Promise<void>;
}) {
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<number | null>(null);

  async function load() {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const list = await authApi.pendingUsersRequest(token);
      setUsers(list);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao carregar pendentes");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [token]);

  async function handleDecision(
    u: User,
    decision: "approve" | "reject",
    role?: Role,
    organizationalUnit?: OrganizationalUnit,
  ) {
    if (!token) return;
    setActionId(u.id);
    setError(null);
    try {
      await authApi.approveUserRequest(token, u.id, {
        decision,
        role: decision === "approve" ? role : undefined,
        organizational_unit: decision === "approve" ? organizationalUnit : undefined,
      });
      await load();
      void refreshUser();
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro na operação");
    } finally {
      setActionId(null);
    }
  }

  return (
    <section className="space-y-4">
      <h3 className="text-lg font-semibold text-zinc-100">Cadastros pendentes</h3>
      {error && (
        <div className="rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-200">{error}</div>
      )}
      <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950/70">
        {loading ? (
          <p className="p-6 text-sm text-zinc-400">Carregando fila…</p>
        ) : users.length === 0 ? (
          <p className="p-6 text-sm text-zinc-400">Nenhum cadastro pendente.</p>
        ) : (
          <table className="min-w-full divide-y divide-zinc-800 text-sm">
            <thead className="bg-black/40 text-left text-xs uppercase tracking-wide text-zinc-500">
              <tr>
                <th className="px-4 py-3">E-mail</th>
                <th className="px-4 py-3">Patente</th>
                <th className="px-4 py-3">Nome guerra</th>
                <th className="px-4 py-3">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-900">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-zinc-900/40">
                  <td className="px-4 py-3 text-zinc-300">{u.email}</td>
                  <td className="px-4 py-3 text-zinc-200">{u.patente}</td>
                  <td className="px-4 py-3 text-zinc-200">{u.nome_guerra}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                      <select
                        id={`role-${u.id}`}
                        defaultValue="BRACAL"
                        className="rounded-md border border-zinc-800 bg-zinc-900 px-2 py-1 text-xs text-zinc-100"
                        aria-label="Role"
                      >
                        {ROLES.map((r) => (
                          <option key={r} value={r}>
                            {r}
                          </option>
                        ))}
                      </select>
                      <select
                        id={`unit-${u.id}`}
                        defaultValue="FIRST_PLATOON"
                        className="rounded-md border border-zinc-800 bg-zinc-900 px-2 py-1 text-xs text-zinc-100"
                        aria-label="Pelotão"
                      >
                        {UNITS.map((unit) => (
                          <option key={unit} value={unit}>
                            {ORGANIZATIONAL_UNIT_LABELS[unit]}
                          </option>
                        ))}
                      </select>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          disabled={actionId === u.id}
                          onClick={() => {
                            const roleSel = document.getElementById(`role-${u.id}`) as HTMLSelectElement;
                            const unitSel = document.getElementById(`unit-${u.id}`) as HTMLSelectElement;
                            void handleDecision(
                              u,
                              "approve",
                              roleSel.value as Role,
                              unitSel.value as OrganizationalUnit,
                            );
                          }}
                          className="rounded-md border border-zinc-600 px-3 py-1 text-xs text-zinc-100 hover:bg-zinc-900 disabled:opacity-50"
                        >
                          Aprovar
                        </button>
                        <button
                          type="button"
                          disabled={actionId === u.id}
                          onClick={() => void handleDecision(u, "reject")}
                          className="rounded-md border border-zinc-800 px-3 py-1 text-xs text-zinc-400 hover:border-red-900 hover:text-red-200 disabled:opacity-50"
                        >
                          Rejeitar
                        </button>
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}

function AfastamentosPendentesSection({ token }: { token: string | null }) {
  const [rows, setRows] = useState<VacationRequestPublic[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    setErr(null);
    try {
      const data = await absencesApi.listPendingAbsences(token);
      setRows(data);
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : "Erro ao carregar fila");
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  const act = async (id: number, kind: "approve" | "reject", reason: string) => {
    if (!token) return;
    setBusyId(id);
    setMsg(null);
    try {
      if (kind === "approve") {
        await absencesApi.approveAbsence(token, id, reason || null);
      } else {
        await absencesApi.rejectAbsence(token, id, reason);
      }
      setMsg("Atualizado.");
      await load();
    } catch (e) {
      setMsg(e instanceof ApiError ? e.detail : "Falha na decisão");
    } finally {
      setBusyId(null);
    }
  };

  const formatPeriod = (start: string, end: string) => {
    const s = new Date(start + "T12:00:00").toLocaleDateString("pt-BR");
    const e = new Date(end + "T12:00:00").toLocaleDateString("pt-BR");
    return `${s} → ${e}`;
  };

  return (
    <section className="space-y-4">
      <h3 className="text-lg font-semibold text-zinc-100">Afastamentos pendentes</h3>
      <p className="text-sm text-zinc-500">
        Férias/LP com revisão de simultaneidade e demais tipos aguardam deferimento do comando.
      </p>
      {err && <p className="text-sm text-red-400">{err}</p>}
      {msg && <p className="text-sm text-emerald-400">{msg}</p>}
      <ul className="space-y-3">
        {rows.map((r) => (
          <li
            key={r.id}
            className="rounded-xl border border-zinc-800/80 bg-black/35 p-4 shadow-inner shadow-black/20"
          >
            <header className="flex flex-wrap items-start justify-between gap-3">
              <section>
                <p className="text-sm font-medium text-zinc-100">
                  {r.patente} {r.nome_guerra}{" "}
                  <span className="text-zinc-500">· {formatPeriod(r.start_date, r.end_date)}</span>
                </p>
                <p className="mt-1 text-xs text-zinc-500">
                  {vacationTypeLabel(r.vacation_type)} · {r.total_days} dias · ID #{r.id}
                </p>
                {r.review_reason && (
                  <p className="mt-2 text-xs text-amber-200/90">Revisão automática: {r.review_reason}</p>
                )}
              </section>
              <span
                className={[
                  "rounded border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
                  vacationStatusBadgeClass(r.status),
                ].join(" ")}
              >
                {vacationStatusLabel(r.status)}
              </span>
            </header>
            <VacationDecisionRow
              disabled={busyId === r.id}
              onApprove={(m) => void act(r.id, "approve", m)}
              onReject={(m) => void act(r.id, "reject", m)}
            />
          </li>
        ))}
        {rows.length === 0 && !err && <p className="text-sm text-zinc-500">Nenhuma solicitação pendente.</p>}
      </ul>
    </section>
  );
}

function VacationDecisionRow({
  disabled,
  onApprove,
  onReject,
}: {
  disabled: boolean;
  onApprove: (reason: string) => void;
  onReject: (reason: string) => void;
}) {
  const [reason, setReason] = useState("");
  return (
    <footer className="mt-4 flex flex-col gap-2 border-t border-zinc-800/80 pt-3 sm:flex-row sm:items-end">
      <label className="flex-1 text-xs text-zinc-500">
        Motivo / observação (obrigatório para indeferir)
        <input
          className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 px-2 py-1.5 text-sm text-zinc-100"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Texto operacional"
        />
      </label>
      <section className="flex gap-2">
        <button
          type="button"
          disabled={disabled}
          onClick={() => onApprove(reason)}
          className="rounded border border-emerald-800/80 bg-emerald-950/40 px-3 py-2 text-xs font-medium text-emerald-100 hover:bg-emerald-900/40 disabled:opacity-50"
        >
          Deferir
        </button>
        <button
          type="button"
          disabled={disabled || !reason.trim()}
          onClick={() => onReject(reason)}
          className="rounded border border-red-800/80 bg-red-950/40 px-3 py-2 text-xs font-medium text-red-100 hover:bg-red-900/40 disabled:opacity-50"
        >
          Indeferir
        </button>
      </section>
    </footer>
  );
}

function FolgasPendentesSection({ token }: { token: string | null }) {
  const [rows, setRows] = useState<LeaveRequestPublic[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    setErr(null);
    try {
      const data = await leavesApi.listPendingLeaves(token);
      setRows(data);
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : "Erro ao carregar fila");
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  const act = async (id: number, kind: "approve" | "reject", motivo: string) => {
    if (!token) return;
    setBusyId(id);
    setMsg(null);
    try {
      if (kind === "approve") {
        await leavesApi.approveLeave(token, id, motivo || null);
      } else {
        await leavesApi.rejectLeave(token, id, motivo);
      }
      setMsg("Atualizado.");
      await load();
    } catch (e) {
      setMsg(e instanceof ApiError ? e.detail : "Falha na decisão");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <section className="space-y-4">
      <h3 className="text-lg font-semibold text-zinc-100">Folgas pendentes</h3>
      <p className="text-sm text-zinc-500">
        Folgas em análise ou com revisão automática (limite mensal / efetivo) aguardam deferimento explícito.
      </p>
      {err && <p className="text-sm text-red-400">{err}</p>}
      {msg && <p className="text-sm text-emerald-400">{msg}</p>}
      <ul className="space-y-3">
        {rows.map((r) => (
          <li
            key={r.id}
            className="rounded-xl border border-zinc-800/80 bg-black/35 p-4 shadow-inner shadow-black/20"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-zinc-100">
                  {r.patente} {r.nome_guerra}{" "}
                  <span className="text-zinc-500">
                    · {new Date(r.leave_on + "T12:00:00").toLocaleDateString("pt-BR")}
                  </span>
                </p>
                <p className="mt-1 text-xs text-zinc-500">
                  {leaveTypeLabel(r.leave_type)} · ID #{r.id}
                </p>
                {r.review_reason && (
                  <p className="mt-2 text-xs text-amber-200/90">Revisão automática: {r.review_reason}</p>
                )}
              </div>
              <span
                className={[
                  "rounded border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
                  leaveStatusBadgeClass(r.status),
                ].join(" ")}
              >
                {leaveStatusLabel(r.status)}
              </span>
            </div>
            <LeaveDecisionRow
              disabled={busyId === r.id}
              onApprove={(m) => void act(r.id, "approve", m)}
              onReject={(m) => void act(r.id, "reject", m)}
            />
          </li>
        ))}
        {rows.length === 0 && !err && <p className="text-sm text-zinc-500">Nenhuma folga pendente.</p>}
      </ul>
    </section>
  );
}

function LeaveDecisionRow({
  disabled,
  onApprove,
  onReject,
}: {
  disabled: boolean;
  onApprove: (motivo: string) => void;
  onReject: (motivo: string) => void;
}) {
  const [motivo, setMotivo] = useState("");
  return (
    <div className="mt-4 flex flex-col gap-2 border-t border-zinc-800/80 pt-3 sm:flex-row sm:items-end">
      <label className="flex-1 text-xs text-zinc-500">
        Motivo / observação (obrigatório para indeferir)
        <input
          className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 px-2 py-1.5 text-sm text-zinc-100"
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
          placeholder="Texto operacional"
        />
      </label>
      <div className="flex gap-2">
        <button
          type="button"
          disabled={disabled}
          onClick={() => onApprove(motivo)}
          className="rounded border border-emerald-800/80 bg-emerald-950/40 px-3 py-2 text-xs font-medium text-emerald-100 hover:bg-emerald-900/40 disabled:opacity-50"
        >
          Deferir
        </button>
        <button
          type="button"
          disabled={disabled || !motivo.trim()}
          onClick={() => onReject(motivo)}
          className="rounded border border-red-800/80 bg-red-950/40 px-3 py-2 text-xs font-medium text-red-100 hover:bg-red-900/40 disabled:opacity-50"
        >
          Indeferir
        </button>
      </div>
    </div>
  );
}

function CompensacoesApprovalSection({ token }: { token: string | null }) {
  const [pending, setPending] = useState<CompensationEventPublic[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const loadPending = useCallback(async () => {
    if (!token) return;
    try {
      const rows = await compensationsApi.listPendingCompensations(token);
      setPending(rows);
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : "Erro ao carregar pendências");
    }
  }, [token]);

  useEffect(() => {
    void loadPending();
  }, [loadPending]);

  const decide = useCallback(
    async (id: number, kind: "approve" | "reject", motivoText: string) => {
      if (!token) return;
      setErr(null);
      setMsg(null);
      try {
        if (kind === "approve") {
          await compensationsApi.approveCompensationEvent(token, id, motivoText || null);
        } else {
          await compensationsApi.rejectCompensationEvent(token, id, motivoText);
        }
        setMsg("Decisão registrada.");
        await loadPending();
      } catch (ex) {
        setErr(ex instanceof ApiError ? ex.detail : "Erro na decisão");
      }
    },
    [token, loadPending],
  );

  return (
    <section className="space-y-6">
      <p className="text-sm text-zinc-400">
        Criação em <a href="/compensacoes" className="text-sky-400 underline">Compensações</a>. Aqui só aprovação.
      </p>
      {err && <p className="text-sm text-red-400">{err}</p>}
      {msg && <p className="text-sm text-emerald-400">{msg}</p>}
      <div className="rounded-xl border border-zinc-800/80 bg-zinc-950/40 p-6">
        <h4 className="text-sm font-semibold uppercase tracking-wider text-zinc-300">Pendências de comando</h4>
        <ul className="mt-4 space-y-4">
          {pending.map((ev) => (
            <li key={ev.id} className="rounded-lg border border-zinc-800/60 bg-black/30 p-4">
              <div>
                <p className="text-sm font-medium text-zinc-100">{COMPENSATION_TYPE_LABELS[ev.event_type]}</p>
                <p className="mt-1 text-xs text-zinc-500">Evento #{ev.id}</p>
                {ev.created_by_label && (
                  <p className="mt-1 text-xs text-zinc-500">Registrado por: {ev.created_by_label}</p>
                )}
                <p className="mt-2 whitespace-pre-wrap text-xs text-zinc-300">{ev.motivo}</p>
                <p className="mt-2 text-[10px] uppercase tracking-wide text-zinc-500">
                  Envolvidos: {ev.participant_user_ids.join(", ")}
                </p>
              </div>
              <CompEventDecisionRow
                onApprove={(m) => void decide(ev.id, "approve", m)}
                onReject={(m) => void decide(ev.id, "reject", m)}
              />
            </li>
          ))}
          {pending.length === 0 && <p className="text-sm text-zinc-500">Nenhum evento pendente.</p>}
        </ul>
      </div>
    </section>
  );
}

function CompEventDecisionRow({
  onApprove,
  onReject,
}: {
  onApprove: (motivo: string) => void;
  onReject: (motivo: string) => void;
}) {
  const [motivo, setMotivo] = useState("");
  return (
    <div className="mt-4 flex flex-col gap-2 border-t border-zinc-800/80 pt-3 sm:flex-row sm:items-end">
      <label className="flex-1 text-xs text-zinc-500">
        Motivo (obrigatório para indeferir)
        <input
          className="mt-1 w-full rounded border border-zinc-800 bg-zinc-950 px-2 py-1.5 text-sm text-zinc-100"
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
        />
      </label>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => onApprove(motivo)}
          className="rounded border border-emerald-800/80 bg-emerald-950/40 px-3 py-2 text-xs font-medium text-emerald-100"
        >
          Deferir
        </button>
        <button
          type="button"
          disabled={!motivo.trim()}
          onClick={() => onReject(motivo)}
          className="rounded border border-red-800/80 bg-red-950/40 px-3 py-2 text-xs font-medium text-red-100 disabled:opacity-50"
        >
          Indeferir
        </button>
      </div>
    </div>
  );
}

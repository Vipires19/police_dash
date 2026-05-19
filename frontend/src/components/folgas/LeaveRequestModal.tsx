import { useEffect, useState } from "react";
import { ApiError } from "@/services/api";
import * as compensationsApi from "@/services/compensationsApi";
import { useAuth } from "@/hooks/AuthContext";
import { leaveTypeLabel } from "@/components/folgas/leaveTypeLabels";
import type { LeaveType, UserCompensationAvailable } from "@/types/leaves";

interface Props {
  open: boolean;
  dateIso: string | null;
  token: string | null;
  availableCredits: UserCompensationAvailable[];
  onClose: () => void;
  onSubmit: (payload: {
    leave_on: string;
    leave_type: LeaveType;
    user_compensation_id?: number | null;
  }) => Promise<void>;
}

function creditSummary(c: UserCompensationAvailable): string {
  const dt = new Date(c.event_date + "T12:00:00").toLocaleDateString("pt-BR");
  const short = c.description.length > 72 ? `${c.description.slice(0, 72)}…` : c.description;
  return `${c.label} · ${dt} — ${short}`;
}

const LEAVE_TYPES: LeaveType[] = ["MONTHLY", "COMPENSATION", "DS"];

export function LeaveRequestModal({ open, dateIso, token, availableCredits, onClose, onSubmit }: Props) {
  const { user } = useAuth();
  const [leaveType, setLeaveType] = useState<LeaveType>("MONTHLY");
  const [creditId, setCreditId] = useState<number | "">("");
  const [dsUsage, setDsUsage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!open || leaveType !== "DS" || !token || !user) {
      setDsUsage(null);
      return;
    }
    let cancelled = false;
    void compensationsApi.getDsUsage(token, user.id).then((u) => {
      if (!cancelled) setDsUsage(u.display);
    });
    return () => {
      cancelled = true;
    };
  }, [open, leaveType, token, user]);

  if (!open || !dateIso) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      await onSubmit({
        leave_on: dateIso,
        leave_type: leaveType,
        user_compensation_id: leaveType === "COMPENSATION" ? (creditId === "" ? null : Number(creditId)) : null,
      });
      setLeaveType("MONTHLY");
      setCreditId("");
      onClose();
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : e instanceof Error ? e.message : "Erro ao solicitar");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-xl border border-zinc-700 bg-zinc-950 p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.3em] text-zinc-500">Solicitação</p>
            <h3 className="mt-1 text-lg font-semibold text-zinc-50">Folga operacional</h3>
            <p className="mt-1 text-sm text-zinc-400">Dia {new Date(dateIso + "T12:00:00").toLocaleDateString("pt-BR")}</p>
          </div>
          <button type="button" onClick={onClose} className="rounded border border-zinc-700 px-2 py-1 text-xs text-zinc-400 hover:text-white">Fechar</button>
        </div>
        <form className="mt-6 space-y-4" onSubmit={(e) => void handleSubmit(e)}>
          <div>
            <p className="text-xs font-medium text-zinc-400">Tipo</p>
            <div className="mt-2 space-y-2">
              {LEAVE_TYPES.map((t) => (
                <label key={t} className="flex cursor-pointer items-center gap-2 rounded-lg border border-zinc-800 bg-black/40 px-3 py-2 text-sm">
                  <input type="radio" name="lt" checked={leaveType === t} onChange={() => { setLeaveType(t); if (t !== "COMPENSATION") setCreditId(""); }} disabled={t === "COMPENSATION" && availableCredits.length === 0} />
                  {leaveTypeLabel(t)}
                </label>
              ))}
            </div>
          </div>
          {leaveType === "DS" && dsUsage && <p className="text-sm text-sky-300">{dsUsage} — referência visual (sem bloqueio automático)</p>}
          {leaveType === "COMPENSATION" && (
            <div>
              <label className="text-xs font-medium text-zinc-400" htmlFor="credit">Crédito de compensação aprovado</label>
              <select id="credit" className="mt-1 w-full rounded-lg border border-zinc-800 bg-black/50 px-3 py-2 text-sm text-zinc-100" value={creditId} onChange={(e) => setCreditId(e.target.value === "" ? "" : Number(e.target.value))} required>
                <option value="">Selecione o crédito…</option>
                {availableCredits.map((c) => (<option key={c.id} value={c.id}>{creditSummary(c)}</option>))}
              </select>
            </div>
          )}
          {err && <p className="text-sm text-red-400">{err}</p>}
          <button type="submit" disabled={busy || (leaveType === "COMPENSATION" && creditId === "")} className="w-full rounded-lg border border-zinc-500 bg-zinc-100 py-2 text-sm font-semibold text-zinc-900 disabled:opacity-50">{busy ? "Enviando…" : "Solicitar"}</button>
        </form>
      </div>
    </div>
  );
}

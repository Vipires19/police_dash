import { useCallback, useEffect, useState } from "react";
import { OperationalLayout } from "@/layouts/OperationalLayout";
import { OrgUnitBadge, orgBadgeVariantForViewer } from "@/components/OrgUnitBadge";
import { useAuth } from "@/hooks/AuthContext";
import { ApiError } from "@/services/api";
import * as usersApi from "@/services/usersApi";
import { ORGANIZATIONAL_UNIT_LABELS, isStaffEditor } from "@/types";

const PATENTES_SELECT = [
  "1° TEN",
  "2° TEN",
  "SUBTEN",
  "1° SGT",
  "2° SGT",
  "3° SGT",
  "CB",
  "SD",
];

export function PerfilPage() {
  const { token, user, refreshUser } = useAuth();
  const [form, setForm] = useState<usersApi.UserProfilePatch>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  const showActive = user ? isStaffEditor(user.role) : false;

  const hydrate = useCallback(async () => {
    if (!token || !user) return;
    setLoading(true);
    setError(null);
    try {
      const me = await usersApi.getUser(token, user.id);
      setForm({
        full_name: me.full_name,
        re: me.re,
        address: me.address,
        phone: me.phone,
        birth_date: me.birth_date ? me.birth_date.slice(0, 10) : null,
        blood_type: me.blood_type,
        patente: me.patente,
        nome_guerra: me.nome_guerra,
        is_active: me.is_active,
      });
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao carregar perfil");
    } finally {
      setLoading(false);
    }
  }, [token, user]);

  useEffect(() => {
    void hydrate();
  }, [hydrate]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !user) return;
    setSaving(true);
    setError(null);
    setOk(null);
    try {
      const patch: usersApi.UserProfilePatch = { ...form };
      if (!showActive) {
        delete patch.is_active;
      }
      await usersApi.patchUser(token, user.id, patch);
      setOk("Perfil atualizado.");
      void refreshUser();
      await hydrate();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Erro ao salvar");
    } finally {
      setSaving(false);
    }
  }

  return (
    <OperationalLayout>
      <header className="mb-8">
        <p className="text-xs uppercase tracking-[0.35em] text-zinc-500">Conta</p>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-semibold text-zinc-50 sm:text-3xl">Meu perfil</h1>
          {user && <OrgUnitBadge variant={orgBadgeVariantForViewer(user)} />}
        </div>
        <p className="mt-2 text-sm text-zinc-400">
          Dados operacionais. Perfis de comando podem alternar status ativo quando aplicável.
        </p>
        {user && (
          <p className="mt-2 text-xs text-zinc-500">
            Pelotão: {ORGANIZATIONAL_UNIT_LABELS[user.organizational_unit]} · Role: {user.role}
          </p>
        )}
      </header>

      {error && (
        <div className="mb-4 rounded-md border border-red-900/50 bg-red-950/40 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}
      {ok && (
        <div className="mb-4 rounded-md border border-emerald-900/50 bg-emerald-950/30 px-4 py-3 text-sm text-emerald-200">
          {ok}
        </div>
      )}

      {loading || !user ? (
        <p className="text-sm text-zinc-500">Carregando…</p>
      ) : (
        <form
          onSubmit={(e) => void onSubmit(e)}
          className="mx-auto max-w-lg space-y-4 rounded-xl border border-zinc-800/80 bg-zinc-950/60 p-6 shadow-inner shadow-black/30"
        >
          <div>
            <label className="text-xs uppercase text-zinc-500">E-mail (somente leitura)</label>
            <p className="mt-1 rounded-md border border-zinc-800/60 bg-black/40 px-3 py-2 text-sm text-zinc-400">
              {user.email}
            </p>
          </div>
          <div>
            <label className="text-xs uppercase text-zinc-500">Nome completo</label>
            <input
              className="mt-1 w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
              value={form.full_name ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value || null }))}
            />
          </div>
          <div>
            <label className="text-xs uppercase text-zinc-500">Nome de guerra</label>
            <input
              required
              minLength={1}
              className="mt-1 w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
              value={form.nome_guerra ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, nome_guerra: e.target.value }))}
            />
          </div>
          <div>
            <label className="text-xs uppercase text-zinc-500">RE</label>
            <input
              className="mt-1 w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 font-mono text-sm"
              value={form.re ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, re: e.target.value || null }))}
            />
          </div>
          <div>
            <label className="text-xs uppercase text-zinc-500">Endereço</label>
            <textarea
              className="mt-1 w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
              rows={2}
              value={form.address ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, address: e.target.value || null }))}
            />
          </div>
          <div>
            <label className="text-xs uppercase text-zinc-500">Telefone</label>
            <input
              className="mt-1 w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
              value={form.phone ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value || null }))}
            />
          </div>
          <div>
            <label className="text-xs uppercase text-zinc-500">Data de nascimento</label>
            <input
              type="date"
              className="mt-1 w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
              value={form.birth_date ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, birth_date: e.target.value || null }))}
            />
          </div>
          <div>
            <label className="text-xs uppercase text-zinc-500">Tipo sanguíneo</label>
            <input
              className="mt-1 w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
              value={form.blood_type ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, blood_type: e.target.value || null }))}
            />
          </div>
          <div>
            <label className="text-xs uppercase text-zinc-500">Patente</label>
            <select
              className="mt-1 w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
              value={form.patente ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, patente: e.target.value }))}
            >
              <option value="">Selecione…</option>
              {PATENTES_SELECT.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
              {form.patente && !PATENTES_SELECT.includes(form.patente) && (
                <option value={form.patente}>{form.patente} (atual)</option>
              )}
            </select>
          </div>
          {showActive && (
            <label className="flex items-center gap-2 text-sm text-zinc-300">
              <input
                type="checkbox"
                checked={Boolean(form.is_active)}
                onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
              />
              Ativo no sistema
            </label>
          )}
          <button
            type="submit"
            disabled={saving}
            className="w-full rounded-lg border border-zinc-500 bg-zinc-100 py-2.5 text-sm font-semibold text-zinc-900 hover:bg-white disabled:opacity-50"
          >
            {saving ? "Salvando…" : "Salvar alterações"}
          </button>
        </form>
      )}
    </OperationalLayout>
  );
}

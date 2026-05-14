import {
  DndContext,
  type DragEndEvent,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import { SortableContext, arrayMove, sortableKeyboardCoordinates, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { useCallback, useEffect, useMemo, useState } from "react";
import { OperationalLayout } from "@/layouts/OperationalLayout";
import { SortablePoliceRow } from "@/components/SortablePoliceRow";
import { useAuth } from "@/hooks/AuthContext";
import type { User } from "@/types";
import { isStaffEditor } from "@/types";
import { patenteRank } from "@/constants/ranks";
import { ApiError } from "@/services/api";
import * as usersApi from "@/services/usersApi";

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

function buildGroups(users: User[]): { patenteDb: string; users: User[] }[] {
  const groups: { patenteDb: string; users: User[] }[] = [];
  for (const u of users) {
    const key = u.patente.trim().toLowerCase();
    const last = groups[groups.length - 1];
    if (!last || last.users[0]!.patente.trim().toLowerCase() !== key) {
      groups.push({ patenteDb: u.patente.trim(), users: [u] });
    } else {
      last.users.push(u);
    }
  }
  return groups;
}

function sortUsersLikeBackend(users: User[]): User[] {
  return [...users].sort((a, b) => {
    const ra = patenteRank(a.patente);
    const rb = patenteRank(b.patente);
    if (ra !== rb) return ra - rb;
    if (a.display_order !== b.display_order) return a.display_order - b.display_order;
    return a.nome_guerra.localeCompare(b.nome_guerra, "pt-BR");
  });
}

function PatenteBlock({
  patenteDb,
  users,
  canReorder,
  onOpen,
  onReordered,
}: {
  patenteDb: string;
  users: User[];
  canReorder: boolean;
  onOpen: (u: User) => void;
  onReordered: (patente: string, ids: number[]) => Promise<void>;
}) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const handleDragEnd = async (event: DragEndEvent) => {
    if (!canReorder) return;
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const ids = users.map((u) => String(u.id));
    const oldIndex = ids.indexOf(String(active.id));
    const newIndex = ids.indexOf(String(over.id));
    if (oldIndex < 0 || newIndex < 0) return;
    const next = arrayMove(users, oldIndex, newIndex);
    await onReordered(patenteDb, next.map((u) => u.id));
  };

  return (
    <section className="space-y-3">
      <div className="flex items-baseline justify-between gap-2 border-b border-zinc-800/80 pb-2">
        <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-zinc-400">{patenteDb}</h3>
        <span className="text-xs text-zinc-600">{users.length} policiais</span>
      </div>
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={(e) => void handleDragEnd(e)}>
        <SortableContext items={users.map((u) => String(u.id))} strategy={verticalListSortingStrategy}>
          <div className="flex flex-col gap-2">
            {users.map((u) => (
              <SortablePoliceRow
                key={u.id}
                user={u}
                dragDisabled={!canReorder}
                onOpen={() => onOpen(u)}
              />
            ))}
          </div>
        </SortableContext>
      </DndContext>
    </section>
  );
}

function Drawer({
  open,
  user,
  currentUserId,
  canEditAny,
  onClose,
  onSaved,
}: {
  open: boolean;
  user: User | null;
  currentUserId: number;
  canEditAny: boolean;
  onClose: () => void;
  onSaved: () => Promise<void>;
}) {
  const { token } = useAuth();
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [form, setForm] = useState<usersApi.UserProfilePatch>({});

  useEffect(() => {
    if (!user) return;
    setEditing(false);
    setErr(null);
    setForm({
      full_name: user.full_name,
      re: user.re,
      address: user.address,
      phone: user.phone,
      birth_date: user.birth_date ? user.birth_date.slice(0, 10) : null,
      blood_type: user.blood_type,
      patente: user.patente,
      nome_guerra: user.nome_guerra,
      is_active: user.is_active,
    });
  }, [user]);

  if (!open || !user) return null;

  const isSelf = user.id === currentUserId;
  const canEdit = canEditAny || isSelf;
  const showActiveToggle = canEditAny;

  async function save() {
    if (!token || !user) return;
    setSaving(true);
    setErr(null);
    try {
      const patch: usersApi.UserProfilePatch = { ...form };
      if (!showActiveToggle) {
        delete patch.is_active;
      }
      await usersApi.patchUser(token, user.id, patch);
      await onSaved();
      setEditing(false);
      onClose();
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : "Erro ao salvar");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <button
        type="button"
        className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
        aria-label="Fechar"
        onClick={onClose}
      />
      <aside className="fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col border-l border-zinc-800 bg-zinc-950 shadow-2xl">
        <div className="flex items-start justify-between border-b border-zinc-800 px-4 py-4">
          <div>
            <p className="text-[10px] uppercase tracking-[0.3em] text-zinc-500">Ficha operacional</p>
            <p className="mt-1 text-lg font-semibold text-zinc-50">
              {user.patente} {user.nome_guerra}
            </p>
          </div>
          <button type="button" onClick={onClose} className="rounded-md p-2 text-zinc-400 hover:bg-zinc-900">
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4">
          {err && (
            <div className="mb-4 rounded-md border border-red-900/50 bg-red-950/40 px-3 py-2 text-sm text-red-200">
              {err}
            </div>
          )}

          {!editing ? (
            <dl className="space-y-3 text-sm">
              {[
                ["Nome completo", user.full_name ?? "—"],
                ["Nome de guerra", user.nome_guerra],
                ["RE", user.re ?? "—"],
                ["Endereço", user.address ?? "—"],
                ["Telefone", user.phone ?? "—"],
                ["Nascimento", user.birth_date ? user.birth_date.slice(0, 10) : "—"],
                ["Tipo sanguíneo", user.blood_type ?? "—"],
                ["Patente", user.patente],
                ["Role sistema", user.role],
                ["Status", user.is_active ? "Ativo" : "Inativo"],
              ].map(([k, v]) => (
                <div key={String(k)} className="rounded-lg border border-zinc-800/60 bg-black/30 px-3 py-2">
                  <dt className="text-[10px] uppercase tracking-wider text-zinc-500">{k}</dt>
                  <dd className="mt-1 text-zinc-200">{v}</dd>
                </div>
              ))}
            </dl>
          ) : (
            <div className="space-y-3">
              <label className="block text-xs uppercase text-zinc-500">Nome completo</label>
              <input
                className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
                value={form.full_name ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value || null }))}
              />
              <label className="block text-xs uppercase text-zinc-500">Nome de guerra</label>
              <input
                className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
                value={form.nome_guerra ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, nome_guerra: e.target.value }))}
              />
              <label className="block text-xs uppercase text-zinc-500">RE</label>
              <input
                className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm font-mono"
                value={form.re ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, re: e.target.value || null }))}
              />
              <label className="block text-xs uppercase text-zinc-500">Endereço</label>
              <textarea
                className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
                rows={2}
                value={form.address ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, address: e.target.value || null }))}
              />
              <label className="block text-xs uppercase text-zinc-500">Telefone</label>
              <input
                className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
                value={form.phone ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value || null }))}
              />
              <label className="block text-xs uppercase text-zinc-500">Nascimento</label>
              <input
                type="date"
                className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
                value={form.birth_date ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, birth_date: e.target.value || null }))}
              />
              <label className="block text-xs uppercase text-zinc-500">Tipo sanguíneo</label>
              <input
                className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
                value={form.blood_type ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, blood_type: e.target.value || null }))}
              />
              <label className="block text-xs uppercase text-zinc-500">Patente</label>
              <select
                className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
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
              {showActiveToggle && (
                <label className="flex items-center gap-2 text-sm text-zinc-300">
                  <input
                    type="checkbox"
                    checked={Boolean(form.is_active)}
                    onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
                  />
                  Ativo no sistema
                </label>
              )}
            </div>
          )}
        </div>

        <div className="border-t border-zinc-800 p-4">
          {canEdit && !editing && (
            <button
              type="button"
              onClick={() => setEditing(true)}
              className="w-full rounded-lg border border-zinc-600 py-2 text-sm font-medium text-zinc-100 hover:bg-zinc-900"
            >
              Editar
            </button>
          )}
          {canEdit && editing && (
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setEditing(false)}
                className="flex-1 rounded-lg border border-zinc-800 py-2 text-sm text-zinc-400 hover:bg-zinc-900"
              >
                Cancelar
              </button>
              <button
                type="button"
                disabled={saving}
                onClick={() => void save()}
                className="flex-1 rounded-lg border border-zinc-500 bg-zinc-100 py-2 text-sm font-medium text-zinc-900 hover:bg-white disabled:opacity-50"
              >
                {saving ? "Salvando…" : "Salvar"}
              </button>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}

export function EfetivoPage() {
  const { token, user, refreshUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<User | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const canReorder = user ? isStaffEditor(user.role) : false;

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const list = await usersApi.listEfetivo(token);
      setUsers(sortUsersLikeBackend(list));
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao carregar efetivo");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  const onReordered = useCallback(
    async (patente: string, ids: number[]) => {
      if (!token) return;
      try {
        await usersApi.reorderEfetivo(token, { patente, ordered_user_ids: ids });
        await load();
        void refreshUser();
      } catch (e) {
        setError(e instanceof ApiError ? e.detail : "Erro ao reordenar");
      }
    },
    [token, load, refreshUser],
  );

  const groups = useMemo(() => buildGroups(users), [users]);

  const openDrawer = (u: User) => {
    setSelected(u);
    setDrawerOpen(true);
  };

  return (
    <OperationalLayout>
      <header className="mb-8">
        <p className="text-xs uppercase tracking-[0.35em] text-zinc-500">Pelotão</p>
        <h1 className="mt-2 text-2xl font-semibold text-zinc-50 sm:text-3xl">Efetivo</h1>
        <p className="mt-2 max-w-xl text-sm text-zinc-400">
          Listagem operacional por patente. Comandantes podem arrastar para ajustar antiguidade visual.
        </p>
      </header>

      {error && (
        <div className="mb-6 rounded-md border border-red-900/50 bg-red-950/40 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-sm text-zinc-500">Carregando efetivo…</p>
      ) : (
        <div className="space-y-10">
          {groups.map((g) => (
            <PatenteBlock
              key={g.users.map((u) => u.id).join("-")}
              patenteDb={g.patenteDb}
              users={g.users}
              canReorder={canReorder}
              onOpen={openDrawer}
              onReordered={onReordered}
            />
          ))}
          {users.length === 0 && <p className="text-sm text-zinc-500">Nenhum policial aprovado.</p>}
        </div>
      )}

      <Drawer
        open={drawerOpen}
        user={selected}
        currentUserId={user?.id ?? 0}
        canEditAny={canReorder}
        onClose={() => {
          setDrawerOpen(false);
          setSelected(null);
        }}
        onSaved={async () => {
          await load();
          void refreshUser();
        }}
      />
    </OperationalLayout>
  );
}

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
import { memo, useCallback, useEffect, useMemo, useState } from "react";
import { OperationalLayout } from "@/layouts/OperationalLayout";
import { SortablePoliceRow } from "@/components/SortablePoliceRow";
import { OrgUnitBadge, orgBadgeVariantForUnit, orgBadgeVariantForViewer } from "@/components/OrgUnitBadge";
import { useAuth } from "@/hooks/AuthContext";
import type { OrganizationalUnit, Role, User } from "@/types";
import {
  ALL_ROLES,
  ORGANIZATIONAL_UNITS,
  ORGANIZATIONAL_UNIT_LABELS,
  ORGANIZATIONAL_UNIT_ORDER,
  ORGANIZATIONAL_UNIT_SECTION_LABELS,
  canViewCompanyEfetivo,
  isStaffEditor,
} from "@/types";
import {
  ESTAGIO_SECTION_LABEL,
  type VisualRankGroup,
  VISUAL_GROUP_LABELS,
  patenteRank,
  visualRankGroup,
} from "@/constants/ranks";
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

const ROLES_SELECT: Role[] = ALL_ROLES;
const UNITS_SELECT: OrganizationalUnit[] = ORGANIZATIONAL_UNITS;

const VISUAL_GROUP_ORDER: VisualRankGroup[] = ["OFFICERS", "NCOS", "ENLISTED"];

type PatenteGroup = { patenteDb: string; users: User[] };

type VisualGroup = {
  group: VisualRankGroup;
  label: string;
  patentes: PatenteGroup[];
};

function buildPatenteGroups(users: User[]): PatenteGroup[] {
  const groups: PatenteGroup[] = [];
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

function partitionEfetivoByRole(users: User[]): { operational: User[]; estagio: User[] } {
  const operational: User[] = [];
  const estagio: User[] = [];
  for (const u of users) {
    if (u.role === "ESTAGIO") estagio.push(u);
    else operational.push(u);
  }
  return { operational, estagio };
}

function buildVisualGroups(users: User[]): VisualGroup[] {
  const patenteGroups = buildPatenteGroups(sortUsersLikeBackend(users));
  const byVisual = new Map<VisualRankGroup, PatenteGroup[]>();
  for (const pg of patenteGroups) {
    const vg = visualRankGroup(pg.patenteDb);
    const list = byVisual.get(vg) ?? [];
    list.push(pg);
    byVisual.set(vg, list);
  }
  return VISUAL_GROUP_ORDER.filter((g) => byVisual.has(g)).map((group) => ({
    group,
    label: VISUAL_GROUP_LABELS[group],
    patentes: byVisual.get(group)!,
  }));
}

function buildEfetivoLayout(users: User[]) {
  const { operational, estagio } = partitionEfetivoByRole(users);
  return {
    visualGroups: buildVisualGroups(operational),
    estagioPatentes: buildPatenteGroups(sortUsersLikeBackend(estagio)),
  };
}

function usersForPatenteRank(allUsers: User[], patente: string): User[] {
  const targetRank = patenteRank(patente);
  return sortUsersLikeBackend(allUsers.filter((u) => patenteRank(u.patente) === targetRank));
}

/** Mescla reordenação do bloco visível na ordem completa da patente (inclui ESTAGIO na mesma patente). */
function buildFullPatenteOrder(allUsers: User[], patente: string, reorderedSubsetIds: number[]): number[] {
  const subsetSet = new Set(reorderedSubsetIds);
  const allForPatente = usersForPatenteRank(allUsers, patente);
  if (subsetSet.size === 0) return allForPatente.map((u) => u.id);

  const byId = new Map(allForPatente.map((u) => [u.id, u]));
  const reorderedQueue = reorderedSubsetIds.map((id) => byId.get(id)).filter((u): u is User => u !== undefined);
  let ri = 0;
  return allForPatente.map((u) => {
    if (subsetSet.has(u.id)) {
      return reorderedQueue[ri++]!.id;
    }
    return u.id;
  });
}

function applyPatenteReorder(users: User[], patente: string, fullOrderedIds: number[]): User[] {
  const targetRank = patenteRank(patente);
  const orderMap = new Map(fullOrderedIds.map((id, i) => [id, i]));
  return sortUsersLikeBackend(
    users.map((u) => {
      const idx = orderMap.get(u.id);
      if (patenteRank(u.patente) !== targetRank || idx === undefined) return u;
      return { ...u, display_order: idx };
    }),
  );
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

const PatenteBlock = memo(function PatenteBlock({
  patenteDb,
  users,
  canReorder,
  onOpen,
  onReordered,
  showEstagioBadge = false,
  showUnitBadge = false,
}: {
  patenteDb: string;
  users: User[];
  canReorder: boolean;
  onOpen: (u: User) => void;
  onReordered: (patente: string, ids: number[]) => void;
  showEstagioBadge?: boolean;
  showUnitBadge?: boolean;
}) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const handleDragEnd = (event: DragEndEvent) => {
    if (!canReorder) return;
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const ids = users.map((u) => String(u.id));
    const oldIndex = ids.indexOf(String(active.id));
    const newIndex = ids.indexOf(String(over.id));
    if (oldIndex < 0 || newIndex < 0) return;
    const next = arrayMove(users, oldIndex, newIndex);
    onReordered(patenteDb, next.map((u) => u.id));
  };

  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between gap-2 px-1">
        <h4 className="text-xs font-medium uppercase tracking-[0.15em] text-zinc-500">{patenteDb}</h4>
        <span className="text-[10px] text-zinc-600">{users.length}</span>
      </div>
      <DndContext
        sensors={sensors}
        autoScroll={false}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext items={users.map((u) => String(u.id))} strategy={verticalListSortingStrategy}>
          <div className="flex flex-col gap-2">
            {users.map((u) => (
              <SortablePoliceRow
                key={u.id}
                user={u}
                dragDisabled={!canReorder}
                showEstagioBadge={showEstagioBadge}
                showUnitBadge={showUnitBadge}
                onOpen={() => onOpen(u)}
              />
            ))}
          </div>
        </SortableContext>
      </DndContext>
    </div>
  );
});

function VisualGroupSection({
  label,
  patentes,
  canReorder,
  showUnitBadge,
  onOpen,
  onReordered,
}: {
  label: string;
  patentes: PatenteGroup[];
  canReorder: boolean;
  showUnitBadge: boolean;
  onOpen: (u: User) => void;
  onReordered: (patente: string, ids: number[]) => void;
}) {
  const total = patentes.reduce((n, p) => n + p.users.length, 0);
  return (
    <section className="space-y-5">
      <div className="flex items-baseline justify-between gap-2 border-b border-zinc-700/80 pb-2">
        <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-zinc-300">{label}</h3>
        <span className="text-xs text-zinc-600">{total} policiais</span>
      </div>
      <div className="space-y-6 pl-0 sm:pl-1">
        {patentes.map((p) => (
          <PatenteBlock
            key={p.patenteDb}
            patenteDb={p.patenteDb}
            users={p.users}
            canReorder={canReorder}
            showUnitBadge={showUnitBadge}
            onOpen={onOpen}
            onReordered={onReordered}
          />
        ))}
      </div>
    </section>
  );
}

function EstagioSection({
  patentes,
  canReorder,
  showUnitBadge,
  onOpen,
  onReordered,
}: {
  patentes: PatenteGroup[];
  canReorder: boolean;
  showUnitBadge: boolean;
  onOpen: (u: User) => void;
  onReordered: (patente: string, ids: number[]) => void;
}) {
  const total = patentes.reduce((n, p) => n + p.users.length, 0);
  return (
    <section className="space-y-5 rounded-xl border border-violet-900/40 bg-violet-950/10 p-4 sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-violet-900/30 pb-3">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-violet-200">
            {ESTAGIO_SECTION_LABEL}
          </h3>
          <span className="rounded border border-violet-800/60 bg-violet-950/50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-violet-300">
            Role ESTAGIO
          </span>
        </div>
        <span className="text-xs text-violet-400/80">{total} em estágio</span>
      </div>
      <p className="text-xs text-violet-300/70">
        Policiais com role de estágio, separados do efetivo operacional. A antiguidade continua por patente.
      </p>
      <div className="space-y-6 pl-0 sm:pl-1">
        {patentes.map((p) => (
          <PatenteBlock
            key={p.patenteDb}
            patenteDb={p.patenteDb}
            users={p.users}
            canReorder={canReorder}
            showEstagioBadge
            showUnitBadge={showUnitBadge}
            onOpen={onOpen}
            onReordered={onReordered}
          />
        ))}
      </div>
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
      role: user.role,
      organizational_unit: user.organizational_unit,
    });
  }, [user]);

  if (!open || !user) return null;

  const isSelf = user.id === currentUserId;
  const canEdit = canEditAny || isSelf;
  const showActiveToggle = canEditAny;
  const showRoleSelect = canEditAny && !isSelf;
  const showUnitSelect = canEditAny;

  async function save() {
    if (!token || !user) return;
    setSaving(true);
    setErr(null);
    try {
      const patch: usersApi.UserProfilePatch = { ...form };
      if (!showActiveToggle) {
        delete patch.is_active;
      }
      if (!showRoleSelect) {
        delete patch.role;
      }
      if (!showUnitSelect) {
        delete patch.organizational_unit;
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
            <div className="mt-2">
              <OrgUnitBadge variant={orgBadgeVariantForUnit(user.organizational_unit)} />
            </div>
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
                ["Pelotão", ORGANIZATIONAL_UNIT_LABELS[user.organizational_unit]],
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
              {showRoleSelect && (
                <>
                  <label className="block text-xs uppercase text-zinc-500">Role no sistema</label>
                  <select
                    className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
                    value={form.role ?? ""}
                    onChange={(e) => setForm((f) => ({ ...f, role: e.target.value as Role }))}
                  >
                    {ROLES_SELECT.map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                </>
              )}
              {showUnitSelect && (
                <>
                  <label className="block text-xs uppercase text-zinc-500">Pelotão</label>
                  <select
                    className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
                    value={form.organizational_unit ?? ""}
                    onChange={(e) =>
                      setForm((f) => ({
                        ...f,
                        organizational_unit: e.target.value as OrganizationalUnit,
                      }))
                    }
                  >
                    {UNITS_SELECT.map((unit) => (
                      <option key={unit} value={unit}>
                        {ORGANIZATIONAL_UNIT_LABELS[unit]}
                      </option>
                    ))}
                  </select>
                </>
              )}
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
  const showUnitBadge = user ? canViewCompanyEfetivo(user.role) : false;

  const load = useCallback(async (opts?: { silent?: boolean }) => {
    if (!token) return;
    if (!opts?.silent) setLoading(true);
    setError(null);
    try {
      const list = await usersApi.listEfetivo(token);
      setUsers(sortUsersLikeBackend(list));
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao carregar efetivo");
    } finally {
      if (!opts?.silent) setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  const onReordered = useCallback(
    (patente: string, subsetIds: number[]) => {
      if (!token) return;
      let snapshot: User[] = [];
      let fullIds: number[] = [];
      setUsers((prev) => {
        snapshot = prev;
        fullIds = buildFullPatenteOrder(prev, patente, subsetIds);
        return applyPatenteReorder(prev, patente, fullIds);
      });
      void usersApi
        .reorderEfetivo(token, { patente, ordered_user_ids: fullIds })
        .catch((e) => {
          setUsers(snapshot);
          setError(e instanceof ApiError ? e.detail : "Erro ao reordenar");
        });
    },
    [token],
  );

  const { visualGroups, estagioPatentes } = useMemo(() => buildEfetivoLayout(users), [users]);

  const companyUnitSections = useMemo(() => {
    if (!showUnitBadge) return null;
    return ORGANIZATIONAL_UNIT_ORDER.map((unit) => {
      const unitUsers = users.filter((u) => u.organizational_unit === unit);
      if (unitUsers.length === 0) return null;
      const layout = buildEfetivoLayout(unitUsers);
      return { unit, label: ORGANIZATIONAL_UNIT_SECTION_LABELS[unit], ...layout, count: unitUsers.length };
    }).filter((s): s is NonNullable<typeof s> => s != null);
  }, [users, showUnitBadge]);

  const openDrawer = (u: User) => {
    setSelected(u);
    setDrawerOpen(true);
  };

  return (
    <OperationalLayout>
      <header className="mb-8">
        <p className="text-xs uppercase tracking-[0.35em] text-zinc-500">Companhia</p>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-semibold text-zinc-50 sm:text-3xl">Efetivo</h1>
          {user && (
            <OrgUnitBadge
              variant={
                showUnitBadge ? orgBadgeVariantForViewer(user) : orgBadgeVariantForUnit(user.organizational_unit)
              }
            />
          )}
        </div>
        <p className="mt-2 max-w-xl text-sm text-zinc-400">
          {showUnitBadge
            ? "Efetivo da Companhia organizado por unidade organizacional, com antiguidade por patente."
            : "Efetivo operacional por categoria hierárquica, com seção separada para policiais em estágio. Comandantes podem arrastar para ajustar antiguidade dentro da mesma patente."}
        </p>
      </header>

      {error && (
        <div className="mb-6 rounded-md border border-red-900/50 bg-red-950/40 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-sm text-zinc-500">Carregando efetivo…</p>
      ) : showUnitBadge && companyUnitSections ? (
        <div className="space-y-12">
          {companyUnitSections.map((section) => (
            <div key={section.unit} className="space-y-8">
              <div className="border-y border-zinc-700/70 py-4">
                <div className="flex flex-wrap items-center gap-3">
                  <OrgUnitBadge variant={orgBadgeVariantForUnit(section.unit)} />
                  <h2 className="text-sm font-semibold uppercase tracking-[0.25em] text-zinc-100">
                    {section.label}
                  </h2>
                  <span className="text-xs text-zinc-500">{section.count} policiais</span>
                </div>
              </div>
              {section.visualGroups.map((g) => (
                <VisualGroupSection
                  key={`${section.unit}-${g.group}`}
                  label={g.label}
                  patentes={g.patentes}
                  canReorder={canReorder}
                  showUnitBadge={false}
                  onOpen={openDrawer}
                  onReordered={onReordered}
                />
              ))}
              {section.estagioPatentes.length > 0 && (
                <EstagioSection
                  patentes={section.estagioPatentes}
                  canReorder={canReorder}
                  showUnitBadge={false}
                  onOpen={openDrawer}
                  onReordered={onReordered}
                />
              )}
            </div>
          ))}
          {users.length === 0 && <p className="text-sm text-zinc-500">Nenhum policial encontrado no efetivo.</p>}
        </div>
      ) : (
        <div className="space-y-10">
          {visualGroups.map((g) => (
            <VisualGroupSection
              key={g.group}
              label={g.label}
              patentes={g.patentes}
              canReorder={canReorder}
              showUnitBadge={false}
              onOpen={openDrawer}
              onReordered={onReordered}
            />
          ))}
          {estagioPatentes.length > 0 && (
            <EstagioSection
              patentes={estagioPatentes}
              canReorder={canReorder}
              showUnitBadge={false}
              onOpen={openDrawer}
              onReordered={onReordered}
            />
          )}
          {users.length === 0 && <p className="text-sm text-zinc-500">Nenhum policial encontrado no efetivo.</p>}
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
          await load({ silent: true });
          void refreshUser();
        }}
      />
    </OperationalLayout>
  );
}

import { UserRoundSearch, X } from "lucide-react";
import { useMemo, useState } from "react";
import { useActAs } from "@/hooks/ActAsContext";

type Props = {
  /** Título contextual, ex.: "Compensações". */
  moduleLabel?: string;
};

export function GodModeSelector({ moduleLabel }: Props) {
  const { canUseGodMode, efetivo, targetUser, setTargetUserId, clearTarget, isActingAs } = useActAs();
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return efetivo.slice(0, 40);
    return efetivo
      .filter((u) => {
        const label = `${u.patente} ${u.nome_guerra} ${u.full_name ?? ""} ${u.re ?? ""}`.toLowerCase();
        return label.includes(q);
      })
      .slice(0, 40);
  }, [efetivo, query]);

  if (!canUseGodMode) return null;

  return (
    <div className="mb-6 rounded-lg border border-amber-900/40 bg-amber-950/20 px-4 py-3">
      <div className="flex flex-wrap items-center gap-2">
        <UserRoundSearch className="h-4 w-4 shrink-0 text-amber-400/90" strokeWidth={1.75} />
        <p className="text-sm font-medium text-amber-100/90">Atuar em nome de</p>
        {isActingAs && targetUser && (
          <span className="rounded border border-amber-800/50 bg-amber-950/50 px-2 py-0.5 text-xs text-amber-100">
            {targetUser.patente} {targetUser.nome_guerra}
            {moduleLabel ? ` · ${moduleLabel}` : ""}
          </span>
        )}
        {isActingAs && (
          <button
            type="button"
            onClick={clearTarget}
            className="ml-auto inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-amber-200/80 hover:bg-amber-900/40 hover:text-amber-50"
          >
            <X className="h-3.5 w-3.5" />
            Limpar
          </button>
        )}
      </div>

      <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-start">
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Pesquisar policial..."
          className="w-full rounded-md border border-zinc-700/80 bg-zinc-950/80 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-amber-700/60 focus:outline-none sm:max-w-sm"
          aria-label="Pesquisar policial"
        />
        <select
          value={targetUser?.id ?? ""}
          onChange={(e) => {
            const v = e.target.value;
            setTargetUserId(v ? Number(v) : null);
          }}
          className="w-full rounded-md border border-zinc-700/80 bg-zinc-950/80 px-3 py-2 text-sm text-zinc-100 focus:border-amber-700/60 focus:outline-none sm:max-w-xs"
          aria-label="Selecionar policial"
        >
          <option value="">Eu (ADMIN)</option>
          {filtered.map((u) => (
            <option key={u.id} value={u.id}>
              {u.patente} {u.nome_guerra}
            </option>
          ))}
        </select>
      </div>

      {isActingAs && targetUser && (
        <p className="mt-2 text-xs text-amber-200/70">
          Toda a tela opera como {targetUser.patente} {targetUser.nome_guerra}. A auditoria registra você como
          autor.
        </p>
      )}
    </div>
  );
}

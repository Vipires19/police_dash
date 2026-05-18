import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical } from "lucide-react";
import type { User } from "@/types";

export function SortablePoliceRow({
  user,
  dragDisabled,
  showEstagioBadge = false,
  onOpen,
}: {
  user: User;
  dragDisabled: boolean;
  showEstagioBadge?: boolean;
  onOpen: () => void;
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: String(user.id),
    disabled: dragDisabled,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const inactive = !user.is_active;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={[
        "flex items-stretch gap-2 rounded-lg border border-zinc-800/90 bg-gradient-to-r from-zinc-900/80 to-black/50 shadow-inner shadow-black/20",
        isDragging ? "z-10 opacity-90 ring-1 ring-zinc-500" : "",
        inactive ? "opacity-60" : "",
      ].join(" ")}
    >
      {!dragDisabled && (
        <button
          type="button"
          className="flex w-9 shrink-0 items-center justify-center border-r border-zinc-800/80 text-zinc-500 hover:bg-zinc-900 hover:text-zinc-300"
          aria-label="Arrastar para reordenar"
          {...attributes}
          {...listeners}
        >
          <GripVertical className="h-4 w-4" />
        </button>
      )}
      <button
        type="button"
        onClick={onOpen}
        className="flex min-w-0 flex-1 items-center gap-3 px-3 py-3 text-left transition hover:bg-zinc-900/40"
      >
        <span className="w-24 shrink-0 font-mono text-xs font-semibold uppercase tracking-wide text-zinc-400">
          {user.patente}
        </span>
        <span className="w-28 shrink-0 font-mono text-sm text-zinc-200">{user.re ?? "—"}</span>
        <span className="truncate text-sm font-medium text-zinc-100">{user.nome_guerra}</span>
        {(showEstagioBadge || inactive) && (
          <span className="ml-auto flex shrink-0 items-center gap-2">
            {showEstagioBadge && (
              <span className="rounded border border-violet-800/60 bg-violet-950/50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-violet-300">
                Estágio
              </span>
            )}
            {inactive && (
              <span className="rounded border border-amber-900/50 bg-amber-950/30 px-2 py-0.5 text-[10px] uppercase tracking-wide text-amber-200">
                Inativo
              </span>
            )}
          </span>
        )}
      </button>
    </div>
  );
}

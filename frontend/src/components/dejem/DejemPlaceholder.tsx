type DejemPlaceholderProps = {
  title: string;
  description?: string;
};

export function DejemPlaceholder({ title, description }: DejemPlaceholderProps) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 px-6 py-10">
      <h2 className="text-lg font-semibold text-zinc-100">{title}</h2>
      <p className="mt-2 max-w-lg text-sm text-zinc-400">
        {description ?? "Módulo em desenvolvimento. A estrutura base já está preparada para as próximas fases."}
      </p>
    </div>
  );
}

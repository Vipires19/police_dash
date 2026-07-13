import { Link } from "react-router-dom";
import { OperationalLayout } from "@/layouts/OperationalLayout";
import { useAuth } from "@/hooks/AuthContext";

export function DejemPage() {
  const { isDejemAdmin } = useAuth();

  return (
    <OperationalLayout>
      <header className="mb-8">
        <p className="text-xs uppercase tracking-[0.35em] text-zinc-500">Administrativo</p>
        <h1 className="mt-2 text-2xl font-semibold text-zinc-50">DEJEM</h1>
        <p className="mt-2 max-w-xl text-sm text-zinc-400">
          Organização interna das vagas de DEJEM da Companhia. O cadastro oficial permanece no sistema
          institucional da PM.
        </p>
      </header>

      <nav className="flex flex-wrap gap-3 text-sm">
        <Link
          to="/dejem/my"
          className="rounded-lg border border-zinc-700 px-4 py-2 text-zinc-200 transition-colors hover:border-zinc-500 hover:bg-zinc-900"
        >
          Minha DEJEM
        </Link>
        {isDejemAdmin && (
          <Link
            to="/dejem/admin"
            className="rounded-lg border border-zinc-700 px-4 py-2 text-zinc-200 transition-colors hover:border-zinc-500 hover:bg-zinc-900"
          >
            Manifestação de Interesse
          </Link>
        )}
      </nav>
    </OperationalLayout>
  );
}

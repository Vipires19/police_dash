import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AuthLayout } from "@/layouts/AuthLayout";
import { useAuth } from "@/hooks/AuthContext";
import { ApiError } from "@/services/api";

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [patente, setPatente] = useState("");
  const [nomeGuerra, setNomeGuerra] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register({ email, password, patente, nome_guerra: nomeGuerra });
      navigate("/login", { replace: true, state: { registered: true } });
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Falha no cadastro");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout>
      <form onSubmit={onSubmit} className="space-y-4">
        {error && (
          <div className="rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-200">
            {error}
          </div>
        )}
        <div className="space-y-1">
          <label className="text-xs uppercase tracking-wide text-zinc-500" htmlFor="r-email">
            E-mail
          </label>
          <input
            id="r-email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm outline-none focus:border-zinc-500"
          />
        </div>
        <div className="space-y-1">
          <label className="text-xs uppercase tracking-wide text-zinc-500" htmlFor="r-pass">
            Senha (mín. 8)
          </label>
          <input
            id="r-pass"
            type="password"
            minLength={8}
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm outline-none focus:border-zinc-500"
          />
        </div>
        <div className="space-y-1">
          <label className="text-xs uppercase tracking-wide text-zinc-500" htmlFor="patente">
            Patente
          </label>
          <input
            id="patente"
            required
            value={patente}
            onChange={(e) => setPatente(e.target.value)}
            className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm outline-none focus:border-zinc-500"
          />
        </div>
        <div className="space-y-1">
          <label className="text-xs uppercase tracking-wide text-zinc-500" htmlFor="ng">
            Nome de guerra
          </label>
          <input
            id="ng"
            required
            value={nomeGuerra}
            onChange={(e) => setNomeGuerra(e.target.value)}
            className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm outline-none focus:border-zinc-500"
          />
        </div>
        <button
          type="submit"
          disabled={submitting}
          className="mt-2 w-full rounded-md border border-zinc-600 bg-transparent px-3 py-2 text-sm font-medium text-zinc-100 hover:bg-zinc-900 disabled:opacity-60"
        >
          {submitting ? "Enviando…" : "Enviar para aprovação"}
        </button>
        <p className="text-center text-sm text-zinc-500">
          Já possui acesso?{" "}
          <Link to="/login" className="text-zinc-200 underline-offset-4 hover:underline">
            Voltar ao login
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}

import { useState, type FormEvent } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { AuthLayout } from "@/layouts/AuthLayout";
import { useAuth } from "@/hooks/AuthContext";
import { ApiError } from "@/services/api";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/dashboard";
  const registered = Boolean((location.state as { registered?: boolean } | null)?.registered);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Falha no login");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout>
      <form onSubmit={onSubmit} className="space-y-4">
        {registered && (
          <div className="rounded-md border border-zinc-700 bg-zinc-900/80 px-3 py-2 text-sm text-zinc-200">
            Cadastro recebido. Aguarde aprovação antes do primeiro acesso.
          </div>
        )}
        {error && (
          <div className="rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-200">
            {error}
          </div>
        )}
        <div className="space-y-1">
          <label className="text-xs uppercase tracking-wide text-zinc-500" htmlFor="email">
            E-mail institucional
          </label>
          <input
            id="email"
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none ring-0 focus:border-zinc-500"
          />
        </div>
        <div className="space-y-1">
          <label className="text-xs uppercase tracking-wide text-zinc-500" htmlFor="password">
            Senha
          </label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-zinc-500"
          />
        </div>
        <button
          type="submit"
          disabled={submitting}
          className="mt-2 w-full rounded-md bg-zinc-100 px-3 py-2 text-sm font-medium text-zinc-950 hover:bg-white disabled:opacity-60"
        >
          {submitting ? "Entrando…" : "Entrar"}
        </button>
        <p className="text-center text-sm text-zinc-500">
          Novo acesso?{" "}
          <Link to="/register" className="text-zinc-200 underline-offset-4 hover:underline">
            Solicitar cadastro
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}

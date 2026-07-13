import type { ReactNode } from "react";

export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-zinc-950 to-zinc-950 text-zinc-100">
      <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-4 py-12">
        <div className="mb-8 text-center">
          <p className="text-xs uppercase tracking-[0.35em] text-zinc-500">Acesso restrito</p>
          <h1 className="mt-2 text-2xl font-semibold text-zinc-100">CIA FT</h1>
          <p className="mt-2 text-sm text-zinc-400">Companhia Força Tática/ROCAM — autenticação obrigatória</p>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-6 shadow-[0_0_0_1px_rgba(255,255,255,0.02)] backdrop-blur">
          {children}
        </div>
      </div>
    </div>
  );
}

import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/hooks/AuthContext";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { token, loading, user } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-950 text-zinc-400">
        Carregando…
      </div>
    );
  }

  if (!token || !user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return children;
}

export function ApproverRoute({ children }: { children: ReactNode }) {
  const { isApprover, loading, user } = useAuth();

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-950 text-zinc-400">
        Carregando…
      </div>
    );
  }

  if (!isApprover) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}

/** Central de aprovações: aprovadores ou quem registra eventos de compensação (ex.: BRACAL). */
export function ApprovalHubRoute({ children }: { children: ReactNode }) {
  const { isApprover, canRegisterCompensation, loading, user } = useAuth();

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-950 text-zinc-400">
        Carregando…
      </div>
    );
  }

  if (!isApprover && !canRegisterCompensation) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}

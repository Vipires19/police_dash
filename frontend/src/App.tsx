import type { ReactNode } from "react";
import { createBrowserRouter, Navigate, RouterProvider } from "react-router-dom";
import { AuthProvider, useAuth } from "@/hooks/AuthContext";
import { ApprovalHubRoute, ApproverRoute, ProtectedRoute } from "@/components/ProtectedRoute";
import { LoginPage } from "@/pages/LoginPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { EfetivoPage } from "@/pages/EfetivoPage";
import { FolgasPage } from "@/pages/FolgasPage";
import { PendingUsersPage } from "@/pages/PendingUsersPage";
import { PerfilPage } from "@/pages/PerfilPage";
import { ViaturasPage } from "@/pages/ViaturasPage";

function RootRedirect() {
  const { token, user, loading } = useAuth();
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-950 text-zinc-400">
        Carregando…
      </div>
    );
  }
  if (token && user) {
    return <Navigate to="/dashboard" replace />;
  }
  return <Navigate to="/login" replace />;
}

function GuestShell({ children }: { children: ReactNode }) {
  const { token, user, loading } = useAuth();
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-950 text-zinc-400">
        Carregando…
      </div>
    );
  }
  if (token && user) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
}

const router = createBrowserRouter([
  { path: "/", element: <RootRedirect /> },
  {
    path: "/login",
    element: (
      <GuestShell>
        <LoginPage />
      </GuestShell>
    ),
  },
  {
    path: "/register",
    element: (
      <GuestShell>
        <RegisterPage />
      </GuestShell>
    ),
  },
  {
    path: "/dashboard",
    element: (
      <ProtectedRoute>
        <DashboardPage />
      </ProtectedRoute>
    ),
  },
  {
    path: "/efetivo",
    element: (
      <ProtectedRoute>
        <EfetivoPage />
      </ProtectedRoute>
    ),
  },
  {
    path: "/viaturas",
    element: (
      <ProtectedRoute>
        <ViaturasPage />
      </ProtectedRoute>
    ),
  },
  {
    path: "/perfil",
    element: (
      <ProtectedRoute>
        <PerfilPage />
      </ProtectedRoute>
    ),
  },
  {
    path: "/folgas",
    element: (
      <ProtectedRoute>
        <FolgasPage />
      </ProtectedRoute>
    ),
  },
  {
    path: "/admin/folgas",
    element: (
      <ProtectedRoute>
        <ApproverRoute>
          <Navigate to="/admin/pending-users?tab=folgas" replace />
        </ApproverRoute>
      </ProtectedRoute>
    ),
  },
  {
    path: "/admin/compensacoes",
    element: (
      <ProtectedRoute>
        <ApprovalHubRoute>
          <Navigate to="/admin/pending-users?tab=compensacoes" replace />
        </ApprovalHubRoute>
      </ProtectedRoute>
    ),
  },
  {
    path: "/admin/pending-users",
    element: (
      <ProtectedRoute>
        <ApprovalHubRoute>
          <PendingUsersPage />
        </ApprovalHubRoute>
      </ProtectedRoute>
    ),
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);

export default function App() {
  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  );
}

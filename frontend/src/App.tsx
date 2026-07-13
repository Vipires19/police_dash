import type { ReactNode } from "react";
import { createBrowserRouter, Navigate, RouterProvider } from "react-router-dom";
import { AuthProvider, useAuth } from "@/hooks/AuthContext";
import { ApprovalHubRoute, ApproverRoute, ProtectedRoute } from "@/components/ProtectedRoute";
import { LoginPage } from "@/pages/LoginPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { EfetivoPage } from "@/pages/EfetivoPage";
import { AfastamentosPage } from "@/pages/AfastamentosPage";
import { FeriasPage } from "@/pages/FeriasPage";
import { ServiceScalePage } from "@/pages/ServiceScalePage";
import { FolgasPage } from "@/pages/FolgasPage";
import { PendingUsersPage } from "@/pages/PendingUsersPage";
import { PerfilPage } from "@/pages/PerfilPage";
import { ViaturasPage } from "@/pages/ViaturasPage";
import { CompensationsPage } from "@/pages/CompensationsPage";
import { StolenVehiclesPage } from "@/pages/StolenVehiclesPage";
import { CriminalWatchVehiclesPage } from "@/pages/CriminalWatchVehiclesPage";
import { DejemPage } from "@/pages/DejemPage";
import { DejemAdminPage } from "@/pages/DejemAdminPage";
import { DejemMyPage } from "@/pages/DejemMyPage";

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
    path: "/compensacoes",
    element: (
      <ProtectedRoute>
        <CompensationsPage />
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
    path: "/afastamentos",
    element: (
      <ProtectedRoute>
        <AfastamentosPage />
      </ProtectedRoute>
    ),
  },
  {
    path: "/ferias",
    element: (
      <ProtectedRoute>
        <FeriasPage />
      </ProtectedRoute>
    ),
  },
  {
    path: "/escala-servico",
    element: (
      <ProtectedRoute>
        <ServiceScalePage />
      </ProtectedRoute>
    ),
  },
  {
    path: "/dejem",
    element: (
      <ProtectedRoute>
        <DejemPage />
      </ProtectedRoute>
    ),
  },
  {
    path: "/dejem/admin",
    element: (
      <ProtectedRoute>
        <DejemAdminPage />
      </ProtectedRoute>
    ),
  },
  {
    path: "/dejem/my",
    element: (
      <ProtectedRoute>
        <DejemMyPage />
      </ProtectedRoute>
    ),
  },
  {
    path: "/veiculos-produtos-crime",
    element: (
      <ProtectedRoute>
        <StolenVehiclesPage />
      </ProtectedRoute>
    ),
  },
  {
    path: "/veiculos-c05",
    element: (
      <ProtectedRoute>
        <CriminalWatchVehiclesPage />
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
        <Navigate to="/compensacoes" replace />
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

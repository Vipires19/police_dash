import type { LucideIcon } from "lucide-react";
import {
  ClipboardList,
  LayoutDashboard,
  Menu,
  Shield,
  Truck,
  UserCircle,
  Users,
  X,
} from "lucide-react";
import { useState, type ReactNode } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/AuthContext";

const linkBase =
  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium tracking-wide transition-colors";

export function OperationalLayout({ children }: { children: ReactNode }) {
  const { user, logout, isApprover } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    [
      linkBase,
      isActive
        ? "bg-gradient-to-r from-zinc-800 to-zinc-900 text-zinc-50 ring-1 ring-zinc-600/60"
        : "text-zinc-400 hover:bg-zinc-900/80 hover:text-zinc-100",
    ].join(" ");

  const items: { to: string; label: string; icon: LucideIcon }[] = [
    { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { to: "/efetivo", label: "Efetivo", icon: Users },
    { to: "/viaturas", label: "Viaturas", icon: Truck },
    { to: "/perfil", label: "Perfil", icon: UserCircle },
  ];

  if (isApprover) {
    items.push({ to: "/admin/pending-users", label: "Aprovações", icon: ClipboardList });
  }

  const closeMobile = () => setSidebarOpen(false);

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-zinc-950 via-black to-zinc-950 text-zinc-100">
      {sidebarOpen && (
        <button
          type="button"
          aria-label="Fechar menu"
          className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm lg:hidden"
          onClick={closeMobile}
        />
      )}

      <aside
        className={[
          "fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-zinc-800/90 bg-zinc-950/95 shadow-2xl shadow-black/50 backdrop-blur-md transition-transform duration-200 lg:static lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
        ].join(" ")}
      >
        <div className="flex items-center justify-between border-b border-zinc-800/80 px-4 py-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-zinc-500">Operacional</p>
            <p className="mt-1 text-sm font-semibold leading-tight text-zinc-100">1° Pel FT/ROCAM</p>
          </div>
          <button
            type="button"
            className="rounded-md p-2 text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100 lg:hidden"
            onClick={closeMobile}
            aria-label="Fechar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex flex-1 flex-col gap-1 p-3">
          {items.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} className={linkClass} onClick={closeMobile}>
              <Icon className="h-4 w-4 shrink-0 opacity-80" strokeWidth={1.75} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-zinc-800/80 p-3">
          {user && (
            <div className="mb-3 rounded-lg border border-zinc-800/60 bg-black/40 px-3 py-2">
              <p className="flex items-center gap-2 text-xs font-medium text-zinc-300">
                <Shield className="h-3.5 w-3.5 text-zinc-500" />
                {user.patente} {user.nome_guerra}
              </p>
              <p className="mt-1 text-[10px] uppercase tracking-wider text-zinc-500">{user.role}</p>
            </div>
          )}
          <button
            type="button"
            onClick={handleLogout}
            className="w-full rounded-lg border border-zinc-700/80 px-3 py-2 text-xs font-medium text-zinc-300 transition hover:border-zinc-500 hover:text-white"
          >
            Sair
          </button>
        </div>
      </aside>

      <div className="flex min-h-screen flex-1 flex-col lg:min-w-0">
        <header className="sticky top-0 z-30 flex items-center gap-3 border-b border-zinc-800/80 bg-black/40 px-4 py-3 backdrop-blur lg:hidden">
          <button
            type="button"
            className="rounded-md p-2 text-zinc-300 hover:bg-zinc-900"
            onClick={() => setSidebarOpen(true)}
            aria-label="Abrir menu"
          >
            <Menu className="h-5 w-5" />
          </button>
          <span className="text-sm font-medium text-zinc-200">Painel operacional</span>
        </header>

        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}

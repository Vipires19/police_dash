import type { LucideIcon } from "lucide-react";
import {
  Briefcase,
  CalendarDays,
  CalendarRange,
  Car,
  ChevronDown,
  ClipboardList,
  Gift,
  LayoutDashboard,
  Menu,
  Palmtree,
  Radio,
  ScanSearch,
  Shield,
  Tags,
  Truck,
  UserCircle,
  Users,
  X,
  CalendarClock,
} from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/AuthContext";
import { OrgUnitBadge, orgBadgeVariantForViewer } from "@/components/OrgUnitBadge";
import { PLATFORM_BRAND } from "@/types";

const linkBase =
  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium tracking-wide transition-colors";

const subLinkBase =
  "flex items-center gap-2.5 rounded-lg py-2 pl-9 pr-3 text-sm font-medium tracking-wide transition-colors";

type NavItem = { to: string; label: string; icon: LucideIcon };

type NavGroup = {
  id: string;
  label: string;
  icon: LucideIcon;
  items: NavItem[];
};

function matchNavTarget(pathname: string, search: string, to: string): boolean {
  const [path, queryString] = to.split("?");
  if (path === "/dejem" && (pathname === "/dejem" || pathname.startsWith("/dejem/"))) {
    return true;
  }
  if (pathname !== path) return false;
  if (!queryString) {
    if (path === "/veiculos-c05") {
      const tab = new URLSearchParams(search).get("tab");
      return tab !== "qru";
    }
    return true;
  }
  const expected = new URLSearchParams(queryString);
  const current = new URLSearchParams(search);
  for (const [key, value] of expected.entries()) {
    if (current.get(key) !== value) return false;
  }
  return true;
}

function isGroupActive(pathname: string, search: string, items: NavItem[]): boolean {
  return items.some((item) => matchNavTarget(pathname, search, item.to));
}

function NavGroupSection({
  group,
  pathname,
  search,
  onNavigate,
}: {
  group: NavGroup;
  pathname: string;
  search: string;
  onNavigate: () => void;
}) {
  const groupActive = isGroupActive(pathname, search, group.items);
  const [open, setOpen] = useState(groupActive);

  useEffect(() => {
    if (groupActive) setOpen(true);
  }, [groupActive]);

  const subLinkClass = (to: string) => {
    const active = matchNavTarget(pathname, search, to);
    return [
      subLinkBase,
      active
        ? "bg-gradient-to-r from-zinc-800 to-zinc-900 text-zinc-50 ring-1 ring-zinc-600/60"
        : "text-zinc-500 hover:bg-zinc-900/80 hover:text-zinc-200",
    ].join(" ");
  };

  return (
    <div className="space-y-0.5">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={[
          linkBase,
          "w-full justify-between",
          groupActive ? "text-zinc-200" : "text-zinc-400 hover:bg-zinc-900/80 hover:text-zinc-100",
        ].join(" ")}
        aria-expanded={open}
      >
        <span className="flex items-center gap-3">
          <group.icon className="h-4 w-4 shrink-0 opacity-80" strokeWidth={1.75} />
          {group.label}
        </span>
        <ChevronDown
          className={[
            "h-4 w-4 shrink-0 opacity-60 transition-transform duration-200",
            open ? "rotate-180" : "",
          ].join(" ")}
          strokeWidth={1.75}
        />
      </button>

      <div
        className={[
          "grid transition-[grid-template-rows] duration-200 ease-out",
          open ? "grid-rows-[1fr]" : "grid-rows-[0fr]",
        ].join(" ")}
      >
        <div className="overflow-hidden">
          <div className="space-y-0.5 pb-0.5 pt-0.5">
            {group.items.map(({ to, label, icon: Icon }) => (
              <NavLink key={to} to={to} className={subLinkClass(to)} onClick={onNavigate}>
                <Icon className="h-3.5 w-3.5 shrink-0 opacity-75" strokeWidth={1.75} />
                {label}
              </NavLink>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export function OperationalLayout({ children }: { children: ReactNode }) {
  const { user, logout, isApprover } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
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

  const adminGroup: NavGroup = useMemo(() => {
    const items: NavItem[] = [
      { to: "/escala-servico", label: "Escala de Serviço", icon: CalendarRange },
      { to: "/dejem", label: "DEJEM", icon: CalendarClock },
      { to: "/viaturas", label: "Viaturas", icon: Truck },
    ];
    // Menu Aprovações: apenas roles com poder decisório (ADMIN, CMD_TATICO, TAT_CMD, N90).
    if (isApprover) {
      items.push({ to: "/admin/pending-users", label: "Aprovações", icon: ClipboardList });
    }
    return { id: "admin", label: "Administrativo", icon: Briefcase, items };
  }, [isApprover]);

  const afastamentosGroup: NavGroup = useMemo(
    () => ({
      id: "afastamentos",
      label: "Afastamentos",
      icon: Palmtree,
      items: [
        { to: "/compensacoes", label: "Compensações", icon: Gift },
        { to: "/folgas", label: "Folgas", icon: CalendarDays },
        { to: "/afastamentos", label: "Férias / Licenças", icon: Palmtree },
      ],
    }),
    [],
  );

  const operacionalGroup: NavGroup = useMemo(
    () => ({
      id: "operacional",
      label: "Operacional",
      icon: Radio,
      items: [
        { to: "/veiculos-produtos-crime", label: "Veículos Furto/Roubo", icon: Car },
        { to: "/veiculos-c05", label: "Veículos C05", icon: ScanSearch },
        { to: "/veiculos-c05?tab=qru", label: "Códigos Operacionais", icon: Tags },
      ],
    }),
    [],
  );

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
            <p className="mt-1 text-sm font-semibold leading-tight text-zinc-100">{PLATFORM_BRAND}</p>
            {user && (
              <div className="mt-2">
                <OrgUnitBadge variant={orgBadgeVariantForViewer(user)} />
              </div>
            )}
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

        <nav className="flex flex-1 flex-col gap-1 overflow-y-auto p-3">
          <NavLink to="/dashboard" className={linkClass} onClick={closeMobile}>
            <LayoutDashboard className="h-4 w-4 shrink-0 opacity-80" strokeWidth={1.75} />
            Dashboard
          </NavLink>

          <NavLink to="/efetivo" className={linkClass} onClick={closeMobile}>
            <Users className="h-4 w-4 shrink-0 opacity-80" strokeWidth={1.75} />
            Efetivo
          </NavLink>

          <NavGroupSection
            group={adminGroup}
            pathname={location.pathname}
            search={location.search}
            onNavigate={closeMobile}
          />

          <NavGroupSection
            group={afastamentosGroup}
            pathname={location.pathname}
            search={location.search}
            onNavigate={closeMobile}
          />

          <NavGroupSection
            group={operacionalGroup}
            pathname={location.pathname}
            search={location.search}
            onNavigate={closeMobile}
          />

          <NavLink to="/perfil" className={linkClass} onClick={closeMobile}>
            <UserCircle className="h-4 w-4 shrink-0 opacity-80" strokeWidth={1.75} />
            Perfil
          </NavLink>
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
          <span className="text-sm font-medium text-zinc-200">{PLATFORM_BRAND}</span>
        </header>

        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}

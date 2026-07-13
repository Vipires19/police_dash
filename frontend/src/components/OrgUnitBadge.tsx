import type { OrganizationalUnit, Role, User } from "@/types";

/** Variantes visuais de badge organizacional / escopo. */
export type OrgBadgeVariant =
  | "FIRST_PLATOON"
  | "SECOND_PLATOON"
  | "COMPANY_ADMIN"
  | "COMANDO"
  | "CIA";

export const ORG_BADGE_LABELS: Record<OrgBadgeVariant, string> = {
  FIRST_PLATOON: "1º PELOTÃO",
  SECOND_PLATOON: "2º PELOTÃO",
  COMPANY_ADMIN: "ADMINISTRAÇÃO",
  COMANDO: "COMANDO",
  CIA: "CIA",
};

/** Cores discretas compatíveis com o tema escuro. */
export const ORG_BADGE_CLASS: Record<OrgBadgeVariant, string> = {
  FIRST_PLATOON: "border-sky-800/55 bg-sky-950/35 text-sky-300/90",
  SECOND_PLATOON: "border-emerald-800/55 bg-emerald-950/35 text-emerald-300/90",
  COMPANY_ADMIN: "border-orange-800/55 bg-orange-950/35 text-orange-300/90",
  COMANDO: "border-red-900/55 bg-red-950/35 text-red-300/90",
  CIA: "border-zinc-700/60 bg-zinc-900/50 text-zinc-400",
};

/** Badge de contexto do login (Comando vs unidade). */
export function orgBadgeVariantForViewer(user: Pick<User, "role" | "organizational_unit">): OrgBadgeVariant {
  if (user.role === "ADMIN" || user.role === "CMD_TATICO") return "COMANDO";
  return user.organizational_unit;
}

/** Badge da unidade do policial (sem promover a Comando). */
export function orgBadgeVariantForUnit(unit: OrganizationalUnit): OrgBadgeVariant {
  return unit;
}

export function orgBadgeVariantForRoleAndUnit(
  role: Role,
  unit: OrganizationalUnit,
): OrgBadgeVariant {
  if (role === "ADMIN" || role === "CMD_TATICO") return "COMANDO";
  return unit;
}

const badgeBase =
  "inline-flex shrink-0 items-center rounded border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em]";

export function OrgUnitBadge({
  variant,
  className = "",
}: {
  variant: OrgBadgeVariant;
  className?: string;
}) {
  return (
    <span className={[badgeBase, ORG_BADGE_CLASS[variant], className].filter(Boolean).join(" ")}>
      {ORG_BADGE_LABELS[variant]}
    </span>
  );
}

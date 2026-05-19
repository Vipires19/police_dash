import type { LeaveType } from "@/types/leaves";

export const LEAVE_TYPE_LABELS: Record<LeaveType, string> = {
  MONTHLY: "Folga mensal",
  COMPENSATION: "Compensação",
  DS: "DS (dispensa de serviço)",
};

export function leaveTypeLabel(t: LeaveType): string {
  return LEAVE_TYPE_LABELS[t];
}

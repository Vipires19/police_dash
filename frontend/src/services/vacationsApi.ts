/** @deprecated Use absencesApi — mantido para compatibilidade */
export {
  getAbsenceCalendar as getVacationCalendar,
  listPendingAbsences as listPendingVacations,
  requestAbsence as requestVacation,
  approveAbsence as approveVacation,
  rejectAbsence as rejectVacation,
  cancelAbsence as cancelVacation,
} from "./absencesApi";

export type { AbsenceRequestPayload as VacationRequestPayload } from "./absencesApi";

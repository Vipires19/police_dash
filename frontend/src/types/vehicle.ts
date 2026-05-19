export type VehicleModalidade = "FT" | "ROCAM";
export type VehicleStatus = "OPERANDO" | "BAIXADA" | "MANUTENCAO" | "RESERVA";
export type VehicleActionType = "CREATED" | "STATUS_CHANGED" | "RETURNED" | "UPDATED";

export interface Vehicle {
  id: number;
  placa: string;
  prefixo: string;
  modelo: string;
  modalidade: VehicleModalidade;
  status: VehicleStatus;
  observacoes: string | null;
  baixada_at: string | null;
  retorno_operacao_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface VehicleLog {
  id: number;
  vehicle_id: number;
  user_id: number;
  action_type: VehicleActionType;
  description: string;
  motivo: string | null;
  old_status: VehicleStatus | null;
  new_status: VehicleStatus | null;
  created_at: string;
}

export interface VehicleLogFeedItem extends VehicleLog {
  vehicle_prefixo: string;
  actor_label: string;
}

export interface VehicleCreatePayload {
  placa: string;
  prefixo: string;
  modelo: string;
  modalidade: VehicleModalidade;
  status: VehicleStatus;
}

export interface VehicleStatusPayload {
  new_status: VehicleStatus;
  motivo: string;
}

export interface VehicleUpdatePayload {
  placa?: string;
  prefixo?: string;
  modelo?: string;
  modalidade?: VehicleModalidade;
  status?: VehicleStatus;
  observacoes?: string | null;
  status_motivo?: string;
}

/** Status editáveis no formulário operacional de viaturas. */
export const VEHICLE_EDIT_STATUS_OPTIONS: VehicleStatus[] = [
  "OPERANDO",
  "MANUTENCAO",
  "BAIXADA",
];

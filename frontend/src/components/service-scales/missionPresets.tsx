/**
 * Seletor de missão/empenho — mesmo padrão da Escala Operacional.
 * Reutilizado por ScaleDayDrawer e montagem DEJEM.
 */
import {
  FT_MISSION_PRESETS,
  ROCAM_MISSION_PRESETS,
  type ScaleModality,
} from "@/types/serviceScale";

export function missionToPreset(
  mission: string,
  modality: ScaleModality,
): { preset: string; custom: string } {
  const presets = modality === "FT" ? FT_MISSION_PRESETS : ROCAM_MISSION_PRESETS;
  if ((presets as readonly string[]).includes(mission)) {
    return { preset: mission, custom: "" };
  }
  if (!mission) return { preset: "", custom: "" };
  return { preset: "__custom__", custom: mission };
}

export function resolveMissionName(preset: string, custom: string): string {
  if (preset === "__custom__") return custom.trim();
  return preset.trim();
}

type Props = {
  modality: ScaleModality;
  preset: string;
  custom: string;
  onPresetChange: (value: string) => void;
  onCustomChange: (value: string) => void;
  disabled?: boolean;
  label?: string;
};

export function MissionPresetSelect({
  modality,
  preset,
  custom,
  onPresetChange,
  onCustomChange,
  disabled = false,
  label = "Missão",
}: Props) {
  const presets = modality === "FT" ? FT_MISSION_PRESETS : ROCAM_MISSION_PRESETS;
  return (
    <div className="space-y-1.5">
      <label className="block text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
        {label}
      </label>
      <select
        value={preset}
        disabled={disabled}
        onChange={(e) => onPresetChange(e.target.value)}
        className="w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-2 text-sm text-zinc-100 disabled:opacity-60"
      >
        <option value="">Selecionar missão</option>
        {presets.map((p) => (
          <option key={p} value={p}>
            {p}
          </option>
        ))}
        <option value="__custom__">Personalizado…</option>
      </select>
      {preset === "__custom__" && (
        <input
          value={custom}
          disabled={disabled}
          onChange={(e) => onCustomChange(e.target.value)}
          placeholder="Missão personalizada"
          className="w-full rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 disabled:opacity-60"
        />
      )}
    </div>
  );
}

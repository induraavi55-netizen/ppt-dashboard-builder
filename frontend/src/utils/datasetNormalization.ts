import type { Dataset } from "../types";

/**
 * Mandatory structural layer for dataset normalization.
 * Ensures all dataset objects conform to a strict, predictable, non-nullable structure.
 * deterministic IDs preserve React stability.
 */
export function normalizeDatasets(raw: unknown): Dataset[] {
    if (!Array.isArray(raw)) return [];

    return raw.map((d, index) => ({
        id: d?.id != null ? String(d.id) : `dataset_${index}`,
        name: String(d?.name ?? "Unnamed"),
        preview: Array.isArray(d?.preview) ? d.preview : [],
        row_count: Number(d?.row_count ?? 0),
        col_count: Number(d?.col_count ?? 0),
        detected_type: String(d?.detected_type ?? "unknown"),
        profile: typeof d?.profile === "object" && d?.profile !== null ? d.profile : {}
    }));
}

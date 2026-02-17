import { DEFAULT_PIPELINE_CONFIG, type PipelineConfig } from "../config/defaultPipelineConfig";

export function normalizePipelineConfig(raw: any): PipelineConfig {
    if (!raw || typeof raw !== "object") {
        return DEFAULT_PIPELINE_CONFIG;
    }

    // Handle both snake_case (new) and camelCase (legacy/current backend)
    const rawUseAll = raw.use_all ?? raw.useAll;

    return {
        use_all: typeof rawUseAll === "boolean" ? rawUseAll : true,

        schools: Array.isArray(raw.schools)
            ? raw.schools.map((school: any) => ({
                school_name: school?.school_name ?? school?.schoolName ?? "",
                from_grade: Number(school?.from_grade ?? school?.fromGrade ?? 5),
                to_grade: Number(school?.to_grade ?? school?.toGrade ?? 12)
            }))
            : []
    };
}

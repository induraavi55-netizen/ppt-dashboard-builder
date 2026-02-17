export type SchoolConfig = {
    school_name: string;
    from_grade: number;
    to_grade: number;
};

export type PipelineConfig = {
    use_all: boolean;
    schools: SchoolConfig[];
};

export const DEFAULT_PIPELINE_CONFIG: PipelineConfig = Object.freeze({
    use_all: true,
    schools: []
});

export function normalizePipelineConfig(input: any): PipelineConfig {

    if (!input || typeof input !== "object") {
        return DEFAULT_PIPELINE_CONFIG;
    }

    return {
        use_all: Boolean(input.use_all ?? input.useAll ?? true),
        schools: Array.isArray(input.schools)
            ? input.schools.map((s: any) => ({
                school_name: String(s?.school_name ?? s?.schoolName ?? ""),
                from_grade: Number(s?.from_grade ?? s?.fromGrade ?? 5),
                to_grade: Number(s?.to_grade ?? s?.toGrade ?? 12),
            }))
            : []
    };
}

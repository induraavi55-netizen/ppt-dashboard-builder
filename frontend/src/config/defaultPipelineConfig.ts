export interface SchoolConfig {
    school_name: string;
    from_grade: number;
    to_grade: number;
}

export interface PipelineConfig {
    use_all: boolean;
    schools: SchoolConfig[];
}

export const DEFAULT_PIPELINE_CONFIG: PipelineConfig = Object.freeze({
    use_all: true,
    schools: []
});

export interface Project {
    id: string;
    name: string;
    created_at?: string;
}

export interface Dataset {
    id: string;
    project_id: string;
    name: string;
    detected_type: string;
    row_count: number;
    col_count: number;
    preview: Record<string, any>[];
    schema: any;
    profile: {
        type: string;
        dataset_family: string;
        metric_types: Record<string, string>;
    };
}

export interface UploadResponse {
    project_id: string;
    datasets: Dataset[];
}

export interface ValidationRule {
    id: string;
    label: string;
    check: (datasets: Dataset[]) => boolean | string; // true if pass, string error if fail
    severity: "block" | "warn";
}

export interface PipelineJob {
    id: string;
    step_name: string;
    status: "pending" | "running" | "completed" | "failed";
    output_files: string[];
    error_message?: string;
    logs: string[];
    created_at: string;
    started_at?: string;
    completed_at?: string;
}

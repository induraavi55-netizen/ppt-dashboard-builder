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

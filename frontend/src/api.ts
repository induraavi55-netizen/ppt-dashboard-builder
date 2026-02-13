import axios from "axios";
import type { Dataset } from "./types";

// Access Vite env var or default to localhost
const API_URL = import.meta.env.VITE_API_URL || "https://ppt-dashboard-builder.onrender.com";

const api = axios.create({
    baseURL: API_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

export const uploadData = async (
    file: File,
    projectName: string
): Promise<{ project_id: string; datasets: any[] }> => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("project_name", projectName);

    // Upload endpoint expects multipart
    const res = await api.post("/upload-data", formData, {
        headers: {
            "Content-Type": "multipart/form-data",
        },
    });
    return res.data;
};

export const getProject = async (
    projectId: string
): Promise<{ project: any; datasets: Dataset[] }> => {
    const res = await api.get(`/projects/${projectId}`);
    return res.data;
};

export const exportProject = async (
    projectId: string,
    debugMode: boolean = false
): Promise<Blob> => {
    const res = await api.post(
        `/export/${projectId}`,
        {},
        {
            responseType: "blob", // Important for file download
            headers: {
                "X-EXPORT-DEBUG": debugMode ? "true" : "false",
            },
        }
    );
    return res.data;
};

export const checkTemplateStatus = async (): Promise<{ configured: boolean; source?: string }> => {
    const res = await api.get("/templates/check");
    return res.data;
};

export const uploadTemplate = async (file: File): Promise<{ status: string }> => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await api.post("/templates/upload", formData, {
        headers: {
            "Content-Type": "multipart/form-data",
        },
    });
    return res.data;
};


export const runPipelineStep = async (stepName: string) => {
    const [category, step] = stepName.split('-');
    const res = await api.post(`/pipeline/${category}/step${step}`, {}, {
        headers: {
            "Content-Type": "application/json"
        }
    });
    return res.data;
};

export const getPipelineStatus = async (jobId: string) => {
    const res = await api.get(`/pipeline/status/${jobId}`);
    return res.data;
};

export const getStepPreview = async (stepName: string) => {
    const res = await api.get(`/pipeline/preview/${stepName}`);
    return res.data;
};

export const getPipelineStepPreview = getStepPreview;

export const exportStepOutput = async (stepName: string) => {
    try {
        const response = await api.get(`/pipeline/export/${stepName}`, {
            responseType: 'blob',
        });

        // Extract filename from header or default
        const contentDisposition = response.headers['content-disposition'] || response.headers['Content-Disposition'];
        console.log("Export Headers:", response.headers);

        let filename = `${stepName}_output.zip`;
        const contentType = response.headers['content-type'] || response.headers['Content-Type'];

        if (contentType && (contentType.includes('spreadsheet') || contentType.includes('excel'))) {
            filename = `${stepName}_output.xlsx`;
        }

        if (contentDisposition) {
            const fileNameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
            if (fileNameMatch && fileNameMatch.length === 2)
                filename = fileNameMatch[1];
        }

        // Create a link to download the blob
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();

        // Clean up
        link.parentNode?.removeChild(link);
        window.URL.revokeObjectURL(url);

    } catch (error) {
        console.error("Export failed:", error);
        throw error;
    }
};

export const fetchStepOutput = async (stepName: string): Promise<Blob> => {
    const res = await api.get(`/pipeline/export/${stepName}`, {
        responseType: "blob",
    });
    return res.data;
};

export const getPipelineState = async () => {
    const res = await api.get(`/pipeline/state`);
    return res.data;
};

export const finalizePipeline = async () => {
    const res = await api.post(`/pipeline/finalize`);
    return res.data;
};


export const getPipelineFiles = async () => {
    // Add timestamp to prevent caching
    const res = await api.get(`/pipeline/data-files?t=${new Date().getTime()}`, {
        headers: {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }
    });
    return res.data;
};

export const uploadPipelineData = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post('/pipeline/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return res.data;
};

export const updatePipelineConfig = async (config: { exam_grades: number[], participating_schools: string[] }) => {
    const res = await api.post("/pipeline/config", config);
    return res.data;
};

export const getPipelineConfig = async () => {
    const res = await api.get("/pipeline/config");
    return res.data;
};

export default api;

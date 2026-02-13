import axios from "axios";

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

export default api;

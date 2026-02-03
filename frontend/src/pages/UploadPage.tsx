import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { uploadData } from "../api";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Card, CardContent, CardHeader } from "../components/ui/Card";
import { Spinner } from "../components/ui/Spinner";
import { UploadCloud } from "lucide-react";

export default function UploadPage() {
    const navigate = useNavigate();
    const [projectName, setProjectName] = useState("");
    const [file, setFile] = useState<File | null>(null);
    const [error, setError] = useState<string | null>(null);

    const mutation = useMutation({
        mutationFn: () => {
            if (!file) throw new Error("No file selected");
            if (!projectName) throw new Error("Project name required");
            return uploadData(file, projectName);
        },
        onSuccess: (data) => {
            // Clean up local state maybe? Not needed as we navigate away.
            navigate(`/dashboard/${data.project_id}`, { state: { datasets: data.datasets, projectName } });
        },
        onError: (err: any) => {
            const msg = err.response?.data?.detail || err.message || "Upload failed";
            setError(msg);
        },
    });

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            setFile(e.target.files[0]);
            setError(null);
        }
    };

    const handleUpload = () => {
        if (!projectName.trim()) {
            setError("Please enter a project name.");
            return;
        }
        if (!file) {
            setError("Please select an Excel file.");
            return;
        }
        mutation.mutate();
    };

    return (
        <div className="flex items-center justify-center min-h-screen px-4">
            <Card className="w-full max-w-md">
                <CardHeader className="text-center">
                    <h1 className="text-2xl font-bold text-gray-800">PPT Export Engine</h1>
                    <p className="text-sm text-gray-500">v1.2 Control Panel</p>
                </CardHeader>
                <CardContent className="space-y-6">

                    <div className="space-y-2">
                        <label className="text-sm font-medium">Project Name</label>
                        <Input
                            value={projectName}
                            onChange={(e) => setProjectName(e.target.value)}
                            placeholder="e.g. School Audit 2024"
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium">Data File (.xlsx)</label>
                        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 flex flex-col items-center justify-center cursor-pointer hover:border-blue-500 transition-colors bg-gray-50 hover:bg-white relative">
                            <input
                                type="file"
                                accept=".xlsx"
                                onChange={handleFileChange}
                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                            />
                            <UploadCloud className="h-8 w-8 text-gray-400 mb-2" />
                            <span className="text-sm text-gray-600">
                                {file ? file.name : "Click or Drag file here"}
                            </span>
                        </div>
                    </div>

                    {error && (
                        <div className="p-3 bg-red-50 text-red-700 text-sm rounded-md border border-red-200">
                            {error}
                        </div>
                    )}

                    <Button
                        className="w-full"
                        onClick={handleUpload}
                        disabled={mutation.isPending}
                    >
                        {mutation.isPending ? (
                            <>
                                <Spinner className="mr-2" /> Processing...
                            </>
                        ) : (
                            "Start Upload"
                        )}
                    </Button>

                </CardContent>
            </Card>
        </div>
    );
}

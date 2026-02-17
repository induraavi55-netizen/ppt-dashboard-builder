import { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { PipelineStepButton } from '../components/PipelineStepButton';

import { usePipelineState } from '../hooks/usePipelineState';
import { fetchStepOutput, getPipelineFiles, uploadData, uploadPipelineData, updatePipelineConfig, getPipelineConfig, runPipelineStep, getPipelineStatus } from '../api';
import { useNavigate } from 'react-router-dom';
import { LogViewer } from '../components/LogViewer';
import { DataPreview } from '../components/DataPreview';
import { FileCode, Folder, Upload, AlertCircle, CheckCircle2, Settings, Play, Save, Loader2 } from 'lucide-react';
import { validatePipeline, safeArray } from '../utils/pipelineValidation';

export default function AnalysisPipelinePage() {
    const navigate = useNavigate();
    const { state: pipeline, refresh } = usePipelineState();

    // Debug Instrumentation
    useEffect(() => {
        if (typeof window !== "undefined") {
            window.pipelineDebug = pipeline;
            console.log("Pipeline state:", pipeline);

            if (pipeline) {
                const validation = validatePipeline(pipeline);
                console.groupCollapsed("Pipeline Debug Update");
                console.log("State:", pipeline);
                console.log("Validation:", validation);
                console.groupEnd();
            }
        }
    }, [pipeline]);





    // Upload & Files State
    const [files, setFiles] = useState<string[]>([]);
    const [uploaded, setUploaded] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [uploadError, setUploadError] = useState<string | null>(null);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);

    const [finalizing, setFinalizing] = useState(false);

    // Config State
    const [examGrades, setExamGrades] = useState<string>("5,6,7,8,9,10,11,12");
    const [participatingSchools, setParticipatingSchools] = useState<string>("");
    const [configSaving, setConfigSaving] = useState(false);

    // Run All State
    const [runAllLogs, setRunAllLogs] = useState<string[]>([]);
    const [previewStep, setPreviewStep] = useState<string | null>(null);
    const [runningAll, setRunningAll] = useState(false);
    const [currentStep, setCurrentStep] = useState<number | null>(null);

    // Derived States with Safeguards
    const pipelineValid = useMemo(() => {
        // Safe fallback
        return validatePipeline(pipeline).valid;
    }, [pipeline]);

    // Initial check for existing files - Backend is source of truth
    const checkFiles = async () => {
        try {
            const data = await getPipelineFiles();
            // Strict sync: overwrite state completely
            // Backend now returns uploaded=false if required files are missing
            if (data && data.uploaded) {
                setFiles(safeArray(data.files));
                setUploaded(true);
            } else {
                setFiles([]);
                setUploaded(false);
            }
        } catch (err) {
            console.error("Failed to check files", err);
            setFiles([]);
            setUploaded(false);
        }
    };

    const loadConfig = async () => {
        try {
            const config = await getPipelineConfig();
            if (config) {
                // Safe access to potential nulls
                const grades = safeArray(config.exam_grades || []);
                const schools = safeArray(config.participating_schools || []);
                setExamGrades(grades.join(","));
                setParticipatingSchools(schools.join("\n"));
            }
        } catch (err) {
            console.error("Failed to load config", err);
        }
    }

    useEffect(() => {
        checkFiles();
        loadConfig();
    }, []);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setSelectedFile(e.target.files[0]);
            setUploadError(null);
        }
    };

    const handleUpload = async () => {
        if (!selectedFile) return;

        // 1. Clear State (No optimistic UI)
        setUploading(true);
        setUploadError(null);
        setFiles([]); // Clear old files immediately
        setUploaded(false); // Lock steps immediately

        console.log("Calling upload...", selectedFile.name);

        try {
            const res = await uploadPipelineData(selectedFile);

            console.log("Upload response:", res);

            // 2. Strict Branching
            if (res && res.success) {
                // Determine truth from backend again
                console.log("Calling /pipeline/data-files...");
                await checkFiles();
                setSelectedFile(null); // Optional: clear input
            } else {
                throw new Error((res && res.error) || "Upload failed (unknown error)");
            }

        } catch (err: any) {
            console.error("Upload failed full error:", err);

            let errorMessage = "Upload failed";
            if (axios.isAxiosError(err)) {
                console.error("Axios response data:", err.response?.data);
                // Handle various backend error shapes
                errorMessage =
                    err.response?.data?.detail ||
                    err.response?.data?.error ||
                    err.message ||
                    "Server Error";
            } else if (err.message) {
                errorMessage = err.message;
            }

            setUploadError(errorMessage);

            // State remains cleared/locked
            setFiles([]);
            setUploaded(false);

        } finally {
            setUploading(false);
            // Double check truth to be safe - ALWAYS run this
            console.log("Calling /pipeline/data-files in finally block...");
            await checkFiles();
        }
    };

    const handleFinalize = async () => {
        console.log("Clicked Use Final Dataset");
        setFinalizing(true);
        console.log("Starting finalization...");
        try {
            // Updated Flow:
            // 1. Fetch Blob from Pipeline Output
            // 2. Upload Blob to Project Backend

            console.log("Fetching pipeline output...");
            const blob = await fetchStepOutput("performance-5");

            // Create a File object from the Blob
            const file = new File([blob], "uploadable data.xlsx", { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });

            console.log("Uploading to Dashboard Backend...");
            const res = await uploadData(file, "analysis_pipeline_output");

            console.log("Upload response:", res);

            if (!res || !res.project_id) {
                console.error("Missing project_id in response", res);
                throw new Error("Server returned no project_id");
            }

            console.log(`Redirecting to project ${res.project_id}...`);
            navigate(`/dashboard?project=${res.project_id}`);
        } catch (error: any) {
            console.error("Finalize error:", error);
            alert('Failed to finalize: ' + (error.message || "Unknown error"));
        } finally {
            setFinalizing(false);
        }
    };

    const handleSaveConfig = async () => {
        setConfigSaving(true);
        try {
            const grades = examGrades.split(",").map(s => parseInt(s.trim())).filter(n => !isNaN(n));
            const schools = participatingSchools.split("\n").map(s => s.trim()).filter(s => s.length > 0);

            await updatePipelineConfig({
                exam_grades: grades,
                participating_schools: schools
            });
            alert("Configuration saved!");
        } catch (err) {
            console.error("Failed to save config", err);
            alert("Failed to save configuration");
        } finally {
            setConfigSaving(false);
        }
    };

    const handleRunAll = async () => {
        if (!confirm("This will run all performance analysis steps (0-5) sequentially. Continue?")) return;

        setRunningAll(true);
        try {
            for (let i = 0; i <= 5; i++) {
                setCurrentStep(i);
                console.log(`Running step ${i}...`);
                // Assuming runPipelineStep handles the async call properly
                await runPipelineStep(`performance-${i}`);

                // Poll for completion? or just wait a bit? 
                // The current API returns immediately with job_id. We need to wait for it.
                // For simplicity in this "Run All" feature, we might need a way to wait.
                // HOWEVER, the requirement said "sequentially call endpoints". 
                // If the endpoints return immediately, we can't truly wait without polling.
                // BUT, let's assume for now we just fire them one by one with a small delay or 
                // ideally we should poll. 

                // Let's implement a simple poller here for robustness
                // We need the job ID from runPipelineStep
                // Wait, runPipelineStep returns { job_id, status: "started" }
                // So we can poll.
                // }
                // Actually, wait. The prompt says "await runStep0()", etc. 
                // If the backend runs in background, simply awaiting the POST return isn't enough.
                // But if the previous logic was synchronous, it would be.
                // The existing buttons trigger a background task. 
                // To do this truly sequentially, we MUST poll.

                // Re-implementing correctly:
                // for (let i = 0; i <= 5; i++) {
                //     setCurrentStep(i);
                const res = await runPipelineStep(`performance-${i}`);
                const jobId = res?.job_id;

                if (!jobId) throw new Error("No job ID returned from step " + i);

                // Poll until complete
                while (true) {
                    await new Promise(r => setTimeout(r, 1000)); // 1s delay
                    const statusData = await getPipelineStatus(jobId);

                    if (!statusData) {
                        // Should not happen, but safe guard
                        console.warn("Got null status data, retrying...");
                        continue;
                    }

                    const status = statusData.status;

                    // Update logs if available
                    if (statusData.logs) {
                        // We replace the logs for this step or just show the latest? 
                        // The backend sends full logs array? 
                        // `pipeline_orchestrator.py` sends `active_job_logs[job_id]` which is a list.
                        // We should format them. 
                        // For simplicity in this `Run All` view, we might just append the last log?
                        // Actually, `LogViewer` takes string[]. 
                        // Let's just append new logs. But polling returns ALL logs.
                        // We can just show the logs of the CURRENT running step + history?
                        // Simpler: Just show "Step X: Running..." and let the individual step logs be handled if needed?
                        // User specifically asked for logs.
                        // Let's rely on the final logs or just show status updates.
                        // Better: Just update the `runAllLogs` with the current step's logs.
                        // But since we are polling, we get the WHOLE log list for that job.
                        // We can set `runAllLogs` to be the accumulation of previous steps + current step logs.
                    }

                    if (status === 'completed') {
                        setRunAllLogs(prev => [...prev, `✅ Step ${i} Completed`]);
                        setPreviewStep(`performance-${i}`);
                        // Small delay to let user see the preview before moving on? 
                        // "Pop the preview" implies it should be visible. 
                        // If we move too fast, they won't see it.
                        await new Promise(r => setTimeout(r, 2000));
                        break;
                    }
                    if (status === 'failed') {
                        const errMsg = statusData.error_message || "Unknown error";
                        setRunAllLogs(prev => [...prev, `❌ Step ${i} Failed: ${errMsg}`]);
                        throw new Error(`Step ${i} failed: ${errMsg}`);
                    }
                }

                await refresh(); // Refresh state after each step
            }

            setRunAllLogs(prev => [...prev, "\n✨ ALL STEPS COMPLETED SUCCESSFULLY! ✨"]);
            alert("All steps completed successfully!");

        } catch (err: any) {
            console.error("Run All failed", err);
            let msg = err.message || "Unknown error";
            if (err.response?.data?.detail) {
                msg = err.response.data.detail;
            }
            alert(`Pipeline execution failed: ${msg}`);
            setRunAllLogs(prev => [...prev, `❌ Error: ${msg}`]);
        } finally {
            setRunningAll(false);
            setCurrentStep(null);
        }
    };

    // Helper to identify important files
    const isImportantFile = (name: string) => {
        if (!name) return false;
        if (name === 'REG VS PART.xlsx') return true;
        if (/^Grade\s\d+\.xlsx$/.test(name)) return true;
        if (name.includes('uploadable data.xlsx')) return true;
        return false;
    };

    // Loading Guard - Rendered at the end to ensure hooks are always called
    if (!pipeline || pipeline.status === "loading") {
        return (
            <div className="p-4 flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <Loader2 className="h-8 w-8 animate-spin text-blue-500 mx-auto mb-2" />
                    <p className="text-gray-500">Loading pipeline...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="container mx-auto p-6 max-w-6xl">
            <h1 className="text-3xl font-bold mb-8">Analysis Pipeline</h1>

            {/* Degraded State Warning */}
            {pipeline && !pipelineValid && (
                <div className="mb-8 bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded-r shadow-sm">
                    <div className="flex items-center">
                        <AlertCircle className="h-6 w-6 text-yellow-600 mr-3" />
                        <div>
                            <p className="font-bold text-yellow-700">Pipeline Data Warning</p>
                            <p className="text-sm text-yellow-600">
                                The pipeline state appears to be malformed or incomplete. Some features may be unavailable.
                                <br />
                                <span className="font-mono text-xs opacity-75">Debug info available in console (window.pipelineDebug)</span>
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Upload Section */}
            <section className="mb-12 bg-gray-50 p-6 rounded-lg border border-gray-200">
                <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
                    <Folder className="text-gray-600" />
                    Data Management
                </h2>

                <div className="flex flex-col md:flex-row gap-8">
                    {/* Upload Form */}
                    <div className="flex-1 space-y-4">
                        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Upload Data Folder (ZIP)
                            </label>
                            <div className="flex gap-4 items-center">
                                <input
                                    type="file"
                                    accept=".zip"
                                    onChange={handleFileChange}
                                    className="block w-full text-sm text-gray-500
                                      file:mr-4 file:py-2 file:px-4
                                      file:rounded-full file:border-0
                                      file:text-sm file:font-semibold
                                      file:bg-blue-50 file:text-blue-700
                                      hover:file:bg-blue-100"
                                />
                                <button
                                    onClick={handleUpload}
                                    disabled={!selectedFile || uploading}
                                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                                >
                                    {uploading ? (
                                        <>
                                            <Loader2 size={16} className="animate-spin" />
                                            Uploading...
                                        </>
                                    ) : (
                                        <>
                                            <Upload size={16} />
                                            Upload
                                        </>
                                    )}
                                </button>
                            </div>
                            {uploadError && (
                                <div className="mt-3 text-red-600 text-sm flex items-center gap-2">
                                    <AlertCircle size={16} />
                                    {uploadError}
                                </div>
                            )}
                            <p className="mt-2 text-xs text-gray-500">
                                Required: REG VS PART.xlsx, Grade *.xlsx
                            </p>
                        </div>
                    </div>

                    {/* Detected Files Panel */}
                    <div className="flex-1 bg-white p-4 rounded-lg shadow-sm border border-gray-200 h-64 overflow-y-auto">
                        <h3 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
                            📂 Uploaded Data Detected
                        </h3>
                        {files.length === 0 ? (
                            <div className="text-gray-400 italic text-sm">
                                {uploading ? "Scanning..." : "No files detected. Please upload a ZIP file."}
                            </div>
                        ) : (
                            <ul className="space-y-2">
                                {files.map((file) => {
                                    const important = isImportantFile(file);
                                    return (
                                        <li key={file} className={`flex items-center gap-2 text-sm ${important ? 'font-medium text-green-700' : 'text-gray-600'}`}>
                                            {important ? <CheckCircle2 size={16} className="text-green-600" /> : <FileCode size={16} />}
                                            {file}
                                        </li>
                                    );
                                })}
                            </ul>
                        )}
                    </div>
                </div>
            </section>

            {/* Config Section */}
            <section className="mb-12 bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
                <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2 text-gray-800">
                    <Settings className="text-gray-600" />
                    Configuration
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Exam Grades (comma - separated)
                        </label>
                        <input
                            type="text"
                            value={examGrades}
                            onChange={(e) => setExamGrades(e.target.value)}
                            className="w-full p-2 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                            placeholder="5,6,7,8,9,10,11,12"
                        />
                        <p className="mt-1 text-xs text-gray-500">Example: 5,6,7,8,9,10,11,12</p>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Participating Schools (one per line)
                        </label>
                        <textarea
                            value={participatingSchools}
                            onChange={(e) => setParticipatingSchools(e.target.value)}
                            rows={4}
                            className="w-full p-2 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                            placeholder="School A&#10;School B"
                        />
                    </div>
                </div>
                <div className="mt-4 flex justify-end">
                    <button
                        onClick={handleSaveConfig}
                        disabled={configSaving}
                        className="px-4 py-2 bg-gray-800 text-white rounded hover:bg-gray-900 flex items-center gap-2 disabled:opacity-50"
                    >
                        <Save size={16} />
                        {configSaving ? "Saving..." : "Save Configuration"}
                    </button>
                </div>
            </section>

            {/* Participation Section */}
            <section className={`mb-12 bg-blue-50 p-6 rounded-lg transition-opacity ${!uploaded ? 'opacity-50 pointer-events-none' : ''}`}>
                <h2 className="text-2xl font-semibold mb-4 text-blue-900">
                    📊 Participation Analysis
                </h2>
                <p className="text-gray-600 mb-4">
                    Summarize registration and participation data by school and grade.
                </p>

                <PipelineStepButton
                    stepName="participation-0"
                    label="Run Step 0 - Summarize Participation Data"
                    onComplete={refresh}
                    disabled={!uploaded || runningAll}
                />


            </section>

            {/* Performance Section */}
            <section className={`mb-12 bg-green-50 p-6 rounded-lg transition-opacity ${!uploaded ? 'opacity-50 pointer-events-none' : ''}`}>
                <h2 className="text-2xl font-semibold mb-4 text-green-900">
                    📈 Performance Analysis
                </h2>
                <p className="text-gray-600 mb-4">
                    Process performance data through formatting, pivots, LO/difficulty analysis, and clustering.
                </p>

                <div className="mb-6 p-4 bg-green-100 rounded border border-green-200">
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <h3 className="font-semibold text-green-900">Run All Steps</h3>
                            <p className="text-sm text-green-700">Sequentially execute steps 0 through 5.</p>
                        </div>
                        <button
                            onClick={handleRunAll}
                            disabled={runningAll || !uploaded}
                            className="px-6 py-3 bg-green-600 text-white rounded font-bold shadow hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
                        >
                            {runningAll ? (
                                <>
                                    <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                                    Running Step {currentStep}...
                                </>
                            ) : (
                                <>
                                    <Play size={20} />
                                    Run All Performance Analysis Steps
                                </>
                            )}
                        </button>
                    </div>

                    {/* Run All Output Area */}
                    {(runningAll || runAllLogs.length > 0) && (
                        <div className="space-y-4">
                            {/* Logs */}
                            <div className="bg-white rounded overflow-hidden shadow-sm border border-gray-200">
                                <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                                    Execution Log
                                </div>
                                <LogViewer logs={runAllLogs} className="border-0 mt-0 rounded-none max-h-48" />
                            </div>

                            {/* Active Preview */}
                            {previewStep && (
                                <div className="bg-white rounded overflow-hidden shadow-sm border border-gray-200 animate-in fade-in slide-in-from-top-4 duration-500">
                                    <div className="px-4 py-2 bg-blue-50 border-b border-blue-100 flex justify-between items-center">
                                        <span className="text-sm font-medium text-blue-900">
                                            ✅ Output Preview: {previewStep}
                                        </span>
                                    </div>
                                    <DataPreview stepName={previewStep} />
                                </div>
                            )}
                        </div>
                    )}
                </div>

                <div className="space-y-4">
                    {[
                        { step: 0, label: 'Run Step 0 - Format Performance Data' },
                        { step: 1, label: 'Run Step 1 - Calculate Participation Percentages' },
                        { step: 2, label: 'Run Step 2 - LO-wise Performance' },
                        { step: 3, label: 'Run Step 3 - Difficulty-level Performance' },
                        { step: 4, label: 'Run Step 4 - Subject-level Overall Performance' },
                        { step: 5, label: 'Run Step 5 - Generate Uploadable Dataset' },
                    ].map(({ step, label }) => (
                        <div key={step}>
                            <PipelineStepButton
                                stepName={`performance-${step}`}
                                label={label}
                                onComplete={refresh}
                                disabled={!uploaded || runningAll}
                            />

                        </div>
                    ))}
                </div>
            </section>

            {/* Finalize Section */}
            {pipeline?.final_file_ready && (
                <section className="bg-purple-50 p-6 rounded-lg border-2 border-purple-300">
                    <h2 className="text-2xl font-semibold mb-4 text-purple-900">
                        ✅ Pipeline Complete
                    </h2>
                    <p className="text-gray-700 mb-4">
                        Final dataset ready: <code className="bg-white px-2 py-1 rounded">uploadable data.xlsx</code>
                    </p>
                    <button
                        onClick={handleFinalize}
                        disabled={finalizing}
                        className="bg-purple-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-purple-700 disabled:opacity-50"
                    >
                        {finalizing ? 'Processing...' : '👉 Use Final Dataset for PPT'}
                    </button>
                </section>
            )}
        </div>
    );
}

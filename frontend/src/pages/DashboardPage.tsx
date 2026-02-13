import React, { useState, useMemo } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import type { Dataset } from "../types";
import { exportProject, getProject, checkTemplateStatus, uploadTemplate } from "../api";
import { Button } from "../components/ui/Button";
import { Card, CardHeader, CardContent } from "../components/ui/Card";
import { Spinner } from "../components/ui/Spinner";
import { AlertCircle, CheckCircle, FileText, Download, Upload } from "lucide-react";
import { cn } from "../lib/utils";

class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean; error: Error | null }> {
    constructor(props: any) {
        super(props);
        this.state = { hasError: false, error: null };
    }
    static getDerivedStateFromError(error: Error) {
        return { hasError: true, error };
    }
    componentDidCatch(error: Error, errorInfo: any) {
        console.error("Dashboard Crash:", error, errorInfo);
    }
    render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen flex items-center justify-center bg-gray-50 p-8">
                    <div className="max-w-xl w-full bg-white p-8 rounded-lg shadow-lg border border-red-100 text-center">
                        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
                        <h1 className="text-xl font-bold text-gray-900">Dashboard Crashed</h1>
                        <p className="text-gray-500 mt-2 text-sm">
                            An unexpected error occurred while rendering the dashboard.
                        </p>

                        <div className="mt-6 text-left">
                            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Error Details</div>
                            <pre className="p-3 bg-red-50 text-red-900 rounded text-xs overflow-auto whitespace-pre-wrap max-h-48 border border-red-200 font-mono">
                                {this.state.error?.message}
                                {"\n"}
                                {this.state.error?.stack?.split("\n").slice(0, 3).join("\n")}
                            </pre>
                        </div>

                        <div className="mt-8 flex justify-center gap-4">
                            <Button onClick={() => window.location.href = "/"} variant="secondary">
                                Return to Home
                            </Button>
                            <Button onClick={() => window.location.reload()} variant="primary">
                                Reload Page
                            </Button>
                        </div>
                    </div>
                </div>
            );
        }
        return this.props.children;
    }
}

function DashboardContent() {
    const location = useLocation();
    const navigate = useNavigate();
    const params = new URLSearchParams(location.search);
    const projectId = params.get("project");

    const [debugMode, setDebugMode] = useState(true); // TEMP: Force debug mode
    const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
    const [exportError, setExportError] = useState<string | null>(null);

    // 1. Fetch data if missing in state
    const { data, isLoading, error: fetchError } = useQuery({
        queryKey: ["project", projectId],
        queryFn: () => getProject(projectId!),
        enabled: !!projectId && (!location.state?.datasets || location.state.datasets.length === 0),
        initialData: location.state?.datasets?.length > 0 ? {
            project: { id: projectId!, name: location.state.projectName },
            datasets: location.state.datasets
        } : undefined
    });

    const datasets = (data?.datasets || []) as Dataset[];
    const projectName = (data?.project?.name || location.state?.projectName || "Unknown Project") as string;

    // 2. Template Status
    const { data: templateStatus, refetch: refetchTemplate } = useQuery({
        queryKey: ["template-status"],
        queryFn: checkTemplateStatus,
        refetchOnWindowFocus: true
    });

    const [templateFile, setTemplateFile] = useState<File | null>(null);
    const [templateUploadError, setTemplateUploadError] = useState<string | null>(null);

    const uploadMutation = useMutation({
        mutationFn: uploadTemplate,
        onSuccess: () => {
            setTemplateFile(null);
            setTemplateUploadError(null);
            refetchTemplate();
        },
        onError: (err: any) => {
            setTemplateUploadError(err.response?.data?.detail || "Upload failed");
        }
    });

    // Loading state
    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 text-gray-900">
                <div className="text-center space-y-4">
                    <Spinner className="h-8 w-8 mx-auto" />
                    <p className="text-sm text-gray-500">Loading project context...</p>
                </div>
            </div>
        );
    }

    if (!projectId) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 p-8 text-center">
                <div className="max-w-md space-y-4">
                    <AlertCircle className="h-12 w-12 text-red-500 mx-auto" />
                    <h2 className="text-xl font-bold">Missing Project ID</h2>
                    <p className="text-sm text-gray-500">
                        No project ID provided in URL.
                    </p>
                    <Button onClick={() => navigate("/")} variant="secondary">
                        Return to Upload
                    </Button>
                </div>
            </div>
        );
    }

    // Error state
    if (fetchError || (!isLoading && datasets.length === 0)) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 p-8 text-center">
                <div className="max-w-md space-y-4">
                    <AlertCircle className="h-12 w-12 text-red-500 mx-auto" />
                    <h2 className="text-xl font-bold">Project Not Found.</h2>
                    <p className="text-sm text-gray-500">
                        The project ID might be invalid or the database was reset. Please upload your data again.
                    </p>
                    <div className="flex justify-center space-x-3">
                        <Button onClick={() => navigate("/")} variant="primary">
                            Back to Upload
                        </Button>
                    </div>
                </div>
            </div>
        );
    }

    const issues = useMemo(() => {
        const list: string[] = [];

        datasets.forEach(d => {
            if (!d) return;

            // 1. Empty Check
            if (!d.preview || d.preview.length === 0) {
                list.push(`[BLOCK] Dataset '${d.name}': Empty preview/data.`);
            }

            // 2. Percent Column Check (Profiler-aware)
            // Hardcoded strictly for 'reg_vs_part' or similar if needed, 
            // but relying on detected_type for now.
            const PCT_REQUIRED_TYPES = ["reg_vs_part", "participation_summary"]; // Add types as needed
            const family = d.profile?.dataset_family || d.detected_type || "unknown";
            const metricTypes = d.profile?.metric_types || {};

            if (family && PCT_REQUIRED_TYPES.includes(family)) {
                // Find column that profiler marked as percent
                let percentCol = Object.keys(metricTypes).find(k => metricTypes[k] === "percent");

                // Fallback to strict string scanning if profile information is absent
                if (!percentCol && Object.keys(metricTypes).length === 0) {
                    percentCol = Object.keys(d.preview?.[0] || {}).find(k =>
                        k.toLowerCase().includes("percent") || k.includes("%")
                    );
                }

                if (!percentCol) {
                    list.push(`[BLOCK] Dataset '${d.name}' (${family}): Missing percent column.`);
                }
            }
        });

        return list;
    }, [datasets]);

    const blockingErrors = useMemo(() => {
        const base = issues.filter(i => i.startsWith("[BLOCK]"));

        if (templateStatus && !templateStatus.configured) {
            base.push("[BLOCK] Missing Presentation Template: Upload a PPTX to continue.");
        }

        return base;
    }, [issues, templateStatus]);

    const canExport = blockingErrors.length === 0;


    // ----------------------------------------------------------------
    // EXPORT MUTATION
    // ----------------------------------------------------------------
    const exportMutation = useMutation({
        mutationFn: () => exportProject(projectId!, debugMode),
        onSuccess: (blob) => {
            const url = window.URL.createObjectURL(blob);
            setDownloadUrl(url);
            setExportError(null);

            // Auto trigger download
            const a = document.createElement('a');
            a.href = url;
            const date = new Date().toISOString().split('T')[0];
            a.download = `${projectName.replace(/\s+/g, '_')}_${date}.pptx`;
            document.body.appendChild(a);
            a.click();
            a.remove();
        },
        onError: (err: any) => {
            // Try to read blob as text to get error message if JSON
            if (err.response?.data instanceof Blob) {
                const reader = new FileReader();
                reader.onload = () => {
                    try {
                        const json = JSON.parse(reader.result as string);
                        setExportError(json.detail || "Export failed");
                    } catch (e) {
                        setExportError("Export failed (Blob error)");
                    }
                };
                reader.readAsText(err.response.data);
            } else {
                setExportError(err.message || "Export failed");
            }
        }
    });


    return (
        <div className="min-h-screen bg-gray-50 pb-20">

            {/* Header */}
            <header className="bg-white border-b shadow-sm sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                        <Button variant="ghost" size="sm" onClick={() => navigate("/")}>← Back</Button>
                        <h1 className="text-lg font-bold truncate max-w-md">{projectName}</h1>
                        <span className="text-xs px-2 py-1 bg-gray-100 rounded-full text-gray-600 font-mono">
                            {projectId}
                        </span>
                    </div>
                    <div className="text-sm text-gray-500">
                        {datasets.length} Datasets
                    </div>
                </div>
            </header>


            <main className="max-w-7xl mx-auto px-4 py-8 grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* LEFT COL: INSPECTOR */}
                <div className="lg:col-span-2 space-y-6">
                    <h2 className="text-xl font-semibold flex items-center">
                        <FileText className="mr-2 h-5 w-5 text-gray-500" /> Dataset Inspector
                    </h2>

                    <div className="grid gap-4">
                        {datasets.map((d) => (
                            <DatasetCard key={d.id} dataset={d} />
                        ))}
                    </div>
                </div>

                {/* RIGHT COL: CONTROL PANEL */}
                <div className="space-y-6">

                    {/* VALIDATION PANEL */}
                    <Card>
                        <CardHeader className="bg-gray-50 border-b py-3 px-4">
                            <h3 className="font-semibold text-sm uppercase tracking-wide text-gray-600">
                                Pre-flight Validation
                            </h3>
                        </CardHeader>
                        <CardContent className="p-4">
                            {blockingErrors.length === 0 ? (
                                <div className="text-green-600 flex items-center text-sm font-medium">
                                    <CheckCircle className="h-4 w-4 mr-2" /> All checks passed
                                </div>
                            ) : (
                                <ul className="space-y-2">
                                    {blockingErrors.map((issue, idx) => {
                                        const isBlock = issue.startsWith("[BLOCK]");
                                        return (
                                            <li key={idx} className={cn("text-xs flex items-start p-2 rounded", isBlock ? "bg-red-50 text-red-700" : "bg-yellow-50 text-yellow-700")}>
                                                <AlertCircle className="h-4 w-4 mr-2 shrink-0 mt-0.5" />
                                                <span>{issue.replace("[BLOCK] ", "")}</span>
                                            </li>
                                        );
                                    })}
                                </ul>
                            )}
                        </CardContent>
                    </Card>

                    {/* TEMPLATE PANEL */}
                    <Card>
                        <CardHeader className="bg-gray-50 border-b py-3 px-4">
                            <h3 className="font-semibold text-sm uppercase tracking-wide text-gray-600">
                                Presentation Template
                            </h3>
                        </CardHeader>
                        <CardContent className="p-4 space-y-4">
                            {templateStatus?.configured ? (
                                <div className="p-2 bg-green-50 border border-green-100 rounded flex items-center text-xs text-green-700">
                                    <CheckCircle className="h-4 w-4 mr-2" />
                                    Template loaded via {templateStatus.source === 'env' ? 'Environment' : 'Direct Upload'}
                                </div>
                            ) : (
                                <div className="p-2 bg-yellow-50 border border-yellow-100 rounded flex items-center text-xs text-yellow-700">
                                    <AlertCircle className="h-4 w-4 mr-2" />
                                    No template configured.
                                </div>
                            )}

                            <div className="space-y-4">
                                <div className="flex items-center space-x-2">
                                    <input
                                        type="file"
                                        accept=".pptx"
                                        className="hidden"
                                        id="template-upload"
                                        onChange={(e) => setTemplateFile(e.target.files?.[0] || null)}
                                    />
                                    <label
                                        htmlFor="template-upload"
                                        className="flex-1 flex items-center justify-center border-2 border-dashed border-gray-300 rounded-lg p-4 cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors"
                                    >
                                        <div className="text-center">
                                            <Upload className="mx-auto h-6 w-6 text-gray-400" />
                                            <span className="mt-2 block text-xs font-medium text-gray-900">
                                                {templateFile ? templateFile.name : "Choose PPTX template"}
                                            </span>
                                        </div>
                                    </label>
                                    <Button
                                        size="sm"
                                        disabled={!templateFile || uploadMutation.isPending}
                                        onClick={() => templateFile && uploadMutation.mutate(templateFile)}
                                    >
                                        {uploadMutation.isPending ? <Spinner className="h-4 w-4" /> : "Upload"}
                                    </Button>
                                </div>
                                {templateUploadError && (
                                    <p className="text-[10px] text-red-500">{templateUploadError}</p>
                                )}
                            </div>
                        </CardContent>
                    </Card>

                    {/* EXPORT PANEL */}
                    <Card className={cn(exportError ? "border-red-300" : "")}>
                        <CardHeader className="bg-blue-50 border-b py-3 px-4">
                            <h3 className="font-semibold text-sm uppercase tracking-wide text-blue-800">
                                Export Controls
                            </h3>
                        </CardHeader>
                        <CardContent className="p-4 space-y-6">

                            <label className="flex items-center space-x-2 cursor-pointer select-none">
                                <input
                                    type="checkbox"
                                    className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                    checked={debugMode}
                                    onChange={e => setDebugMode(e.target.checked)}
                                />
                                <div className="text-sm">
                                    <span className="font-medium">Enable QA Mode</span>
                                    <p className="text-xs text-gray-500">Draws debug overlays on slides</p>
                                </div>
                            </label>

                            {exportError && (
                                <div className="text-xs text-red-600 bg-red-50 p-2 rounded">
                                    {exportError}
                                </div>
                            )}

                            <Button
                                className="w-full"
                                size="lg"
                                disabled={!canExport || exportMutation.isPending}
                                onClick={() => exportMutation.mutate()}
                            >
                                {exportMutation.isPending ? (
                                    <><Spinner className="mr-2" /> Generating...</>
                                ) : (
                                    <><Download className="mr-2 h-4 w-4" /> Generate PowerPoint</>
                                )}
                            </Button>

                            {!canExport && (
                                <p className="text-center text-xs text-red-500">
                                    Resolve blocking issues to export.
                                </p>
                            )}

                            {downloadUrl && (
                                <div className="text-center">
                                    <a href={downloadUrl} download className="text-sm text-blue-600 underline hover:text-blue-800">
                                        Click here if download didn't start
                                    </a>
                                </div>
                            )}

                        </CardContent>
                    </Card>

                </div>
            </main >
        </div >
    );
}


function DatasetCard({ dataset }: { dataset: Dataset }) {
    const [expanded, setExpanded] = useState(false);

    // Safeguard against malformed dataset objects
    if (!dataset) return <div className="p-4 text-red-500 text-xs">Invalid Dataset</div>;

    const typeLabel = (dataset.detected_type || "?").substring(0, 2).toUpperCase();
    const rows = dataset.row_count || 0;
    const cols = dataset.col_count || 0;
    const typeName = dataset.detected_type || "Unknown";
    const preview = dataset.preview || [];

    return (
        <Card className="overflow-hidden border transition-shadow hover:shadow-md">
            <div
                className="p-4 flex items-center justify-between cursor-pointer bg-white"
                onClick={() => setExpanded(!expanded)}
            >
                <div className="flex items-center space-x-3 overflow-hidden">
                    <div className="h-8 w-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-xs shrink-0">
                        {typeLabel}
                    </div>
                    <div className="min-w-0">
                        <h4 className="font-medium text-sm truncate" title={dataset.name}>{dataset.name || "Unnamed"}</h4>
                        <p className="text-xs text-gray-500">
                            {rows} rows • {cols} cols • {typeName}
                        </p>
                    </div>
                </div>
                <Button variant="ghost" size="sm" className="text-xs">
                    {expanded ? "Hide" : "peek"}
                </Button>
            </div>

            {expanded && (
                <div className="border-t bg-gray-50 p-4 text-xs overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="border-b">
                                {Object.keys(preview[0] || {}).map((k) => (
                                    <th key={k} className="p-1 font-semibold text-gray-600">{k}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {preview.slice(0, 5).map((row, i) => (
                                <tr key={i} className="border-b last:border-0 border-gray-200">
                                    {Object.values(row || {}).map((val: any, j) => (
                                        <td key={j} className="p-1 text-gray-700 truncate max-w-[150px]" title={String(val)}>
                                            {String(val ?? "")}
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {preview.length === 0 && (
                        <div className="p-2 text-center text-gray-400 italic">No preview data available</div>
                    )}
                    <div className="mt-2 text-gray-400 italic text-center">
                        Showing first {Math.min(preview.length, 5)} rows
                    </div>
                </div>
            )}
        </Card>
    )
}

export default function DashboardPage() {
    return (
        <ErrorBoundary>
            <DashboardContent />
        </ErrorBoundary>
    );
}

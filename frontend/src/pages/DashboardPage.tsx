import { useState, useMemo } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import type { Dataset } from "../types";
import { exportProject, getProject, checkTemplateStatus, uploadTemplate } from "../api";
import { Button } from "../components/ui/Button";
import { Card, CardHeader, CardContent } from "../components/ui/Card";
import { Spinner } from "../components/ui/Spinner";
import { AlertCircle, CheckCircle, FileText, Download, Upload } from "lucide-react";
import { cn } from "../lib/utils";
import { ErrorBoundary } from "../components/common/ErrorBoundary";
import { normalizeDatasets } from "../utils/datasetNormalization";

// --- SUB-COMPONENTS ---

function DatasetCard({ dataset }: { dataset: Dataset }) {
    const [expanded, setExpanded] = useState(false);

    const typeLabel = (dataset.detected_type || "?").substring(0, 2).toUpperCase();
    const preview = dataset.preview;

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
                        <h4 className="font-medium text-sm truncate" title={dataset.name}>{dataset.name}</h4>
                        <p className="text-xs text-gray-500">
                            {dataset.row_count} rows • {dataset.col_count} cols • {dataset.detected_type}
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
    );
}

function DatasetInspector({ datasets }: { datasets: Dataset[] }) {
    return (
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
    );
}

function TemplateControls() {
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

    return (
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
    );
}

function ExportControls({ projectId, projectName, datasets, templateConfigured }: {
    projectId: string;
    projectName: string;
    datasets: Dataset[];
    templateConfigured: boolean;
}) {
    const [debugMode, setDebugMode] = useState(true);
    const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
    const [exportError, setExportError] = useState<string | null>(null);

    const exportMutation = useMutation({
        mutationFn: (args: { projectId: string; debugMode: boolean }) => exportProject(args.projectId, args.debugMode),
        onSuccess: (blob) => {
            const url = window.URL.createObjectURL(blob);
            setDownloadUrl(url);
            setExportError(null);

            const a = document.createElement('a');
            a.href = url;
            const date = new Date().toISOString().split('T')[0];
            a.download = `${projectName.replace(/\s+/g, '_')}_${date}.pptx`;
            document.body.appendChild(a);
            a.click();
            a.remove();
        },
        onError: (err: any) => {
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

    const blockingErrors = useMemo(() => {
        const list: string[] = [];

        datasets.forEach(d => {
            if (!d.preview || d.preview.length === 0) {
                list.push(`Dataset '${d.name}': Empty preview/data.`);
            }

            const PCT_REQUIRED_TYPES = ["reg_vs_part", "participation_summary"];
            if (PCT_REQUIRED_TYPES.includes(d.profile?.dataset_family as string || d.detected_type)) {
                const metricTypes = (d.profile?.metric_types || {}) as Record<string, string>;
                let percentCol = Object.keys(metricTypes).find(k => metricTypes[k] === "percent");

                if (!percentCol) {
                    percentCol = Object.keys(d.preview[0] || {}).find(k =>
                        k.toLowerCase().includes("percent") || k.includes("%")
                    );
                }

                if (!percentCol) {
                    list.push(`Dataset '${d.name}': Missing percent column.`);
                }
            }
        });

        if (!templateConfigured) {
            list.push("Missing Presentation Template: Upload a PPTX to continue.");
        }

        return list;
    }, [datasets, templateConfigured]);

    const canExport = blockingErrors.length === 0;

    return (
        <div className="space-y-6">
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
                            {blockingErrors.map((issue, idx) => (
                                <li key={idx} className="text-xs flex items-start p-2 rounded bg-red-50 text-red-700">
                                    <AlertCircle className="h-4 w-4 mr-2 shrink-0 mt-0.5" />
                                    <span>{issue}</span>
                                </li>
                            ))}
                        </ul>
                    )}
                </CardContent>
            </Card>

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

                    {exportError && <div className="text-xs text-red-600 bg-red-50 p-2 rounded">{exportError}</div>}

                    <Button
                        className="w-full"
                        size="lg"
                        disabled={!canExport || exportMutation.isPending}
                        onClick={() => exportMutation.mutate({ projectId, debugMode })}
                    >
                        {exportMutation.isPending ? <><Spinner className="mr-2" /> Generating...</> : <><Download className="mr-2 h-4 w-4" /> Generate PowerPoint</>}
                    </Button>

                    {!canExport && <p className="text-center text-xs text-red-500">Resolve blocking issues to export.</p>}

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
    );
}

// --- MAIN CONTENT ---

function DashboardContent({ projectId }: { projectId: string }) {
    const location = useLocation();
    const navigate = useNavigate();

    // 1. Fetch data with normalization at the boundary
    const { data, isLoading, error: fetchError } = useQuery({
        queryKey: ["project", projectId],
        queryFn: () => getProject(projectId),
        select: (raw) => {
            const normalizedDatasets = normalizeDatasets(raw?.datasets);
            return {
                project: {
                    id: String(raw?.project?.id ?? projectId),
                    name: String(raw?.project?.name ?? location.state?.projectName ?? "Unknown Project")
                },
                datasets: normalizedDatasets
            };
        },
        initialData: location.state?.datasets?.length > 0 ? {
            project: { id: projectId, name: location.state.projectName },
            datasets: location.state.datasets
        } : undefined
    });

    // 2. Secondary queries
    const { data: templateStatus } = useQuery({
        queryKey: ["template-status"],
        queryFn: checkTemplateStatus
    });

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 text-gray-900">
                <Spinner className="h-8 w-8 mx-auto" />
            </div>
        );
    }

    if (fetchError || (!data?.datasets || data.datasets.length === 0)) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 p-8 text-center">
                <div className="max-w-md space-y-4">
                    <AlertCircle className="h-12 w-12 text-red-500 mx-auto" />
                    <h2 className="text-xl font-bold">Project Not Found.</h2>
                    <Button onClick={() => navigate("/")} variant="primary">Back to Upload</Button>
                </div>
            </div>
        );
    }

    const datasets = data.datasets;
    const projectName = data.project.name;

    return (
        <div className="min-h-screen bg-gray-50 pb-20">
            <header className="bg-white border-b shadow-sm sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                        <Button variant="ghost" size="sm" onClick={() => navigate("/")}>← Back</Button>
                        <h1 className="text-lg font-bold truncate max-w-md">{projectName}</h1>
                        <span className="text-xs px-2 py-1 bg-gray-100 rounded-full text-gray-600 font-mono">{projectId}</span>
                    </div>
                    <div className="text-sm text-gray-500">{datasets.length} Datasets</div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 py-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
                <DatasetInspector datasets={datasets} />
                <div className="space-y-6">
                    <TemplateControls />
                    <ExportControls
                        projectId={projectId}
                        projectName={projectName}
                        datasets={datasets}
                        templateConfigured={!!templateStatus?.configured}
                    />
                </div>
            </main>
        </div>
    );
}

// --- PROJECT GUARD ---

function ProjectGuard({ children }: { children: (projectId: string) => React.ReactNode }) {
    const location = useLocation();
    const navigate = useNavigate();
    const params = new URLSearchParams(location.search);
    const projectId = params.get("project");

    if (!projectId) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 p-8 text-center">
                <div className="max-w-md space-y-4">
                    <AlertCircle className="h-12 w-12 text-red-500 mx-auto" />
                    <h2 className="text-xl font-bold">Missing Project ID</h2>
                    <Button onClick={() => navigate("/")} variant="secondary">Return to Upload</Button>
                </div>
            </div>
        );
    }

    return <>{children(projectId)}</>;
}

// --- PAGE ENTRY ---

export default function DashboardPage() {
    return (
        <ErrorBoundary>
            <ProjectGuard>
                {(projectId) => <DashboardContent projectId={projectId} />}
            </ProjectGuard>
        </ErrorBoundary>
    );
}

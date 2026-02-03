import { useState, useMemo } from "react";
import { useParams, useLocation, useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import type { Dataset } from "../types";
import { exportProject } from "../api";
import { Button } from "../components/ui/Button";
import { Card, CardHeader, CardContent } from "../components/ui/Card";
import { Spinner } from "../components/ui/Spinner";
import { AlertCircle, CheckCircle, FileText, Download } from "lucide-react";
import { cn } from "../lib/utils";

export default function DashboardPage() {
    const { projectId } = useParams<{ projectId: string }>();
    const location = useLocation();
    const navigate = useNavigate();

    // State from navigation or upload
    const datasets = (location.state?.datasets || []) as Dataset[];
    const projectName = (location.state?.projectName || "Unknown Project") as string;

    const [debugMode, setDebugMode] = useState(false);
    const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
    const [exportError, setExportError] = useState<string | null>(null);

    // redirect if no state (MVP limitation)
    if (!datasets || datasets.length === 0) {
        return (
            <div className="p-8 text-center">
                <h2 className="text-xl font-bold">No project context found.</h2>
                <Button onClick={() => navigate("/")} variant="secondary" className="mt-4">
                    Return to Upload
                </Button>
            </div>
        );
    }

    // ----------------------------------------------------------------
    // VALIDATION LOGIC
    // ----------------------------------------------------------------
    const PCT_REQUIRED_TYPES = ["lo", "qlvl", "perf_summary", "subwise", "reg_vs_part_grade"];

    const issues = useMemo(() => {
        const list: string[] = [];

        datasets.forEach(d => {
            // 1. Preview Check
            if (!d.preview || d.preview.length === 0) {
                list.push(`[BLOCK] Dataset '${d.name}': Empty preview/data.`);
            }

            // 2. Percent Column Check
            if (PCT_REQUIRED_TYPES.includes(d.detected_type)) {
                const hasPct = Object.keys(d.preview[0] || {}).some(k =>
                    k.toLowerCase().includes("percent") || k.includes("%")
                );
                if (!hasPct) {
                    list.push(`[BLOCK] Dataset '${d.name}' (${d.detected_type}): Missing percent column.`);
                }
            }
        });

        return list;
    }, [datasets]);

    const blockingErrors = issues.filter(i => i.startsWith("[BLOCK]"));
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
            // Backend sets filename in headers, but we might not access it easily with blob response type in axios without parsing headers.
            // We'll generate a name here or rely on user saving.
            // Actually, let's try to get filename from content-disposition if we change api return type, 
            // but for MVP a generic name + date is fine as per spec "dashboard_v1.2_2026-02-03.pptx"
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
                            {issues.length === 0 ? (
                                <div className="text-green-600 flex items-center text-sm font-medium">
                                    <CheckCircle className="h-4 w-4 mr-2" /> All checks passed
                                </div>
                            ) : (
                                <ul className="space-y-2">
                                    {issues.map((issue, idx) => {
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
            </main>
        </div>
    );
}


function DatasetCard({ dataset }: { dataset: Dataset }) {
    const [expanded, setExpanded] = useState(false);

    return (
        <Card className="overflow-hidden border transition-shadow hover:shadow-md">
            <div
                className="p-4 flex items-center justify-between cursor-pointer bg-white"
                onClick={() => setExpanded(!expanded)}
            >
                <div className="flex items-center space-x-3 overflow-hidden">
                    <div className="h-8 w-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-xs shrink-0">
                        {dataset.detected_type.substring(0, 2).toUpperCase()}
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
                                {Object.keys(dataset.preview[0] || {}).map((k) => (
                                    <th key={k} className="p-1 font-semibold text-gray-600">{k}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {dataset.preview.slice(0, 5).map((row, i) => (
                                <tr key={i} className="border-b last:border-0 border-gray-200">
                                    {Object.values(row).map((val: any, j) => (
                                        <td key={j} className="p-1 text-gray-700 truncate max-w-[150px]" title={String(val)}>
                                            {String(val)}
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    <div className="mt-2 text-gray-400 italic text-center">
                        Showing first 5 rows
                    </div>
                </div>
            )}
        </Card>
    )
}

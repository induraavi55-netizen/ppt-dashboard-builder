import { usePipelineStep } from '../hooks/usePipelineStep';
import { CheckCircle, XCircle, Loader, Download } from 'lucide-react';
import { exportStepOutput } from '../api';
import { useState } from 'react';

interface Props {
    stepName: string;
    label: string;
    onComplete?: () => void;
    disabled?: boolean;
    onBeforeExecute?: () => Promise<void>;
}

import { LogViewer } from './LogViewer';
import { DataPreview } from './DataPreview';

export function PipelineStepButton({ stepName, label, onComplete, disabled, onBeforeExecute }: Props) {
    const { execute, loading, error, completed, logs } = usePipelineStep(stepName, onComplete);
    const [exporting, setExporting] = useState(false);
    const [preflighting, setPreflighting] = useState(false);

    const handleExecute = async () => {
        if (onBeforeExecute) {
            try {
                setPreflighting(true);
                await onBeforeExecute();
            } catch (err) {
                console.error("Pre-execute hook failed:", err);
                return;
            } finally {
                setPreflighting(false);
            }
        }
        execute();
    };

    const handleExport = async (e: React.MouseEvent) => {
        e.stopPropagation();
        setExporting(true);
        try {
            await exportStepOutput(stepName);
        } catch (err) {
            console.error("Failed to export:", err);
            alert("Failed to download output files");
        } finally {
            setExporting(false);
        }
    };

    return (
        <div className="flex flex-col w-full">
            <div className="flex items-center gap-4 p-4 bg-white rounded-lg shadow">
                <button
                    onClick={handleExecute}
                    disabled={loading || preflighting || completed || disabled}
                    className={`
            flex-1 px-4 py-2 rounded font-medium transition
            ${completed ? 'bg-green-100 text-green-800' : 'bg-blue-600 text-white hover:bg-blue-700'}
            ${(loading || preflighting) ? 'opacity-75 cursor-wait' : ''}
            ${disabled ? 'opacity-50 cursor-not-allowed bg-gray-400 hover:bg-gray-400' : ''}
            disabled:cursor-not-allowed
            `}
                >
                    {(loading || preflighting) && <Loader className="inline animate-spin mr-2" size={16} />}
                    {label}
                </button>

                {completed && (
                    <div className="flex items-center gap-2">
                        <CheckCircle className="text-green-600" size={24} />
                        <button
                            onClick={handleExport}
                            disabled={exporting}
                            title="Export Output Files"
                            className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-colors"
                        >
                            {exporting ? (
                                <Loader className="animate-spin" size={20} />
                            ) : (
                                <Download size={20} />
                            )}
                        </button>
                    </div>
                )}

                {error && (
                    <div className="flex items-center gap-2 text-red-600">
                        <XCircle size={24} />
                        <span className="text-sm">{error}</span>
                    </div>
                )}
            </div>

            {/* Logs Area */}
            {(loading || (logs && logs.length > 0)) && (
                <LogViewer logs={logs} className="mx-1" />
            )}

            {/* Data Preview Area */}
            {completed && !error && (
                <DataPreview stepName={stepName} />
            )}
        </div>
    );
}

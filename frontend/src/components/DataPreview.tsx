import { useState, useEffect } from 'react';
import { getPipelineStepPreview } from '../api';
import { FileSpreadsheet, Loader, AlertCircle } from 'lucide-react';

interface Props {
    stepName: string;
}

interface Sheet {
    name: string;
    columns: string[];
    rows: any[];
}

export function DataPreview({ stepName }: Props) {
    const [data, setData] = useState<{ sheets: Sheet[] } | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeSheet, setActiveSheet] = useState<string | null>(null);

    useEffect(() => {
        let mounted = true;

        async function fetchPreview() {
            try {
                setLoading(true);
                const res = await getPipelineStepPreview(stepName);
                if (mounted) {
                    setData(res);
                    if (res?.sheets?.length > 0) {
                        setActiveSheet(res.sheets[0].name);
                    }
                    setLoading(false);
                }
            } catch (err: any) {
                if (mounted) {
                    setError(err.message || 'Failed to load preview');
                    setLoading(false);
                }
            }
        }

        fetchPreview();

        return () => { mounted = false; };
    }, [stepName]);

    if (loading) {
        return (
            <div className="p-4 flex items-center gap-2 text-gray-500">
                <Loader className="animate-spin" size={16} />
                <span>Loading preview...</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-4 flex items-center gap-2 text-red-500 bg-red-50 rounded mt-2">
                <AlertCircle size={16} />
                <span>{error}</span>
            </div>
        );
    }

    if (!data || !data.sheets || data.sheets.length === 0) {
        return null; // No data to show
    }

    const currentSheet = data.sheets.find(s => s.name === activeSheet);

    return (
        <div className="mt-4 border border-gray-200 rounded-lg overflow-hidden bg-white shadow-sm">
            {/* Header / Tabs */}
            <div className="flex items-center gap-2 px-4 py-2 bg-gray-50 border-b border-gray-200 overflow-x-auto">
                <FileSpreadsheet size={16} className="text-green-600 flex-shrink-0" />
                <div className="flex gap-1">
                    {data.sheets.map(sheet => (
                        <button
                            key={sheet.name}
                            onClick={() => setActiveSheet(sheet.name)}
                            className={`
                                px-3 py-1 text-xs font-medium rounded-full transition-colors whitespace-nowrap
                                ${activeSheet === sheet.name
                                    ? 'bg-blue-100 text-blue-700'
                                    : 'text-gray-600 hover:bg-gray-200'}
                            `}
                        >
                            {sheet.name}
                        </button>
                    ))}
                </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto max-h-96">
                {currentSheet && (
                    <table className="min-w-full text-sm text-left">
                        <thead className="bg-gray-50 sticky top-0">
                            <tr>
                                {currentSheet.columns.map((col) => (
                                    <th key={col} className="px-4 py-2 border-b font-medium text-gray-600 whitespace-nowrap">
                                        {col}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {currentSheet.rows.map((row, idx) => (
                                <tr key={idx} className="hover:bg-gray-50 border-b last:border-0 text-sm">
                                    {currentSheet.columns.map((col) => (
                                        <td key={col} className="px-4 py-2 text-gray-700 whitespace-nowrap">
                                            {String(row[col] ?? "")}
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
            <div className="px-4 py-2 bg-gray-50 text-xs text-gray-500 border-t">
                Showing first 10 rows
            </div>
        </div>
    );
}

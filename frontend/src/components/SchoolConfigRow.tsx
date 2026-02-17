import { Trash2 } from "lucide-react";
import { type SchoolConfig } from "../config/defaultPipelineConfig";

interface Props {
    config: SchoolConfig;
    onChange: (config: SchoolConfig) => void;
    onRemove: () => void;
}

const GRADE_OPTIONS = [5, 6, 7, 8, 9, 10, 11, 12];

export function SchoolConfigRow({ config, onChange, onRemove }: Props) {
    return (
        <div className="flex flex-col md:flex-row gap-4 items-start md:items-center bg-gray-50 p-3 rounded border border-gray-200">
            <div className="flex-1 w-full">
                <label className="block text-xs font-semibold text-gray-500 mb-1">School Name</label>
                <input
                    type="text"
                    value={config.school_name}
                    onChange={(e) => onChange({ ...config, school_name: e.target.value })}
                    className="w-full p-2 text-sm border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter school name..."
                />
            </div>

            <div className="flex gap-4 w-full md:w-auto">
                <div className="w-24">
                    <label className="block text-xs font-semibold text-gray-500 mb-1">From Grade</label>
                    <select
                        value={config.from_grade}
                        onChange={(e) => onChange({ ...config, from_grade: Number(e.target.value) })}
                        className="w-full p-2 text-sm border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                    >
                        {GRADE_OPTIONS.map(g => (
                            <option key={g} value={g}>{g}</option>
                        ))}
                    </select>
                </div>

                <div className="w-24">
                    <label className="block text-xs font-semibold text-gray-500 mb-1">To Grade</label>
                    <select
                        value={config.to_grade}
                        onChange={(e) => onChange({ ...config, to_grade: Number(e.target.value) })}
                        className="w-full p-2 text-sm border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                    >
                        {GRADE_OPTIONS.map(g => (
                            <option key={g} value={g}>{g}</option>
                        ))}
                    </select>
                </div>
            </div>

            <button
                onClick={onRemove}
                className="mt-4 md:mt-0 p-2 text-red-600 hover:bg-red-50 rounded transition-colors"
                title="Remove School"
            >
                <Trash2 size={18} />
            </button>
        </div>
    );
}

import { Plus } from "lucide-react";
import { SchoolConfigRow } from "./SchoolConfigRow";
import { type SchoolConfig } from "../config/defaultPipelineConfig";

interface Props {
    configs: SchoolConfig[];
    onChange: (configs: SchoolConfig[]) => void;
    availableSchools?: string[];
}

export function SchoolConfigList({ configs, onChange, availableSchools = [] }: Props) {
    const handleAdd = () => {
        onChange([
            ...configs,
            { school_name: "", from_grade: 5, to_grade: 10 }
        ]);
    };

    const handleUpdate = (index: number, newConfig: SchoolConfig) => {
        const next = [...configs];
        next[index] = newConfig;
        onChange(next);
    };

    const handleRemove = (index: number) => {
        const next = configs.filter((_, i) => i !== index);
        onChange(next);
    };

    return (
        <div className="space-y-4">
            <div className="space-y-3">
                {configs.map((cfg, idx) => (
                    <SchoolConfigRow
                        key={`${cfg.school_name}-${idx}`}
                        config={cfg}
                        onChange={(newCfg) => handleUpdate(idx, newCfg)}
                        onRemove={() => handleRemove(idx)}
                        availableSchools={availableSchools}
                    />
                ))}
            </div>

            <button
                onClick={handleAdd}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded hover:bg-blue-100 transition-colors"
            >
                <Plus size={16} />
                Add School
            </button>
        </div>
    );
}

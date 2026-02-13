import { useState, useEffect } from 'react';
import { getStepPreview } from '../api';

interface PreviewData {
    sheets: Array<{
        name: string;
        columns: string[];
        rows: Record<string, any>[];
    }>;
}

export function useStepPreview(stepName: string, enabled: boolean = true) {
    const [preview, setPreview] = useState<PreviewData | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!enabled) {
            setPreview(null);
            return;
        }

        const fetchPreview = async () => {
            console.log(`[StepPreview] Fetching preview for ${stepName}...`);
            setLoading(true);
            try {
                const data = await getStepPreview(stepName);
                if (!data.error) {
                    console.log(`[StepPreview] Loaded ${stepName}:`, data);
                    setPreview(data);
                } else {
                    console.log(`[StepPreview] No data for ${stepName}:`, data.error);
                }
            } catch (err) {
                console.error(`[StepPreview] Failed to load ${stepName}`, err);
            } finally {
                setLoading(false);
            }
        };

        fetchPreview();
    }, [stepName, enabled]);

    return { preview, loading };
}

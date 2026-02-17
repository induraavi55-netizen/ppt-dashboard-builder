import { useState, useEffect, useCallback } from 'react';
import { getPipelineState } from '../api';
import { DEFAULT_PIPELINE_STATE } from '../utils/pipelineDefaults';

export function usePipelineState() {
    const [state, setState] = useState<any>(DEFAULT_PIPELINE_STATE);

    const refresh = useCallback(async () => {
        try {
            const data = await getPipelineState();
            // Merge with default/current to ensure structure exists if backend returns partial data
            // But usually replace is fine if backend is trusted. 
            // User wants NO CRASH.
            if (data) {
                setState(data);
            } else {
                // Keep default or previous? 
                // If data is null, maybe backend error. 
                // Let's not set to null.
            }
        } catch (err) {
            console.error('Failed to fetch pipeline state:', err);
            // Optionally set error state
        }
    }, []);

    useEffect(() => {
        refresh();
    }, [refresh]);

    return { state, refresh };
}

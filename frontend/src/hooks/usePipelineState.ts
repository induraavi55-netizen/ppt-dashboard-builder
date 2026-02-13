import { useState, useEffect, useCallback } from 'react';
import { getPipelineState } from '../api';

export function usePipelineState() {
    const [state, setState] = useState<any>(null);

    const refresh = useCallback(async () => {
        try {
            const data = await getPipelineState();
            setState(data);
        } catch (err) {
            console.error('Failed to fetch pipeline state:', err);
        }
    }, []);

    useEffect(() => {
        refresh();
    }, [refresh]);

    return { state, refresh };
}

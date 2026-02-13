import { useState, useCallback } from 'react';
import { runPipelineStep, getPipelineStatus } from '../api';

export function usePipelineStep(stepName: string, onComplete?: () => void) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [completed, setCompleted] = useState(false);
    const [logs, setLogs] = useState<string[]>([]);
    const [jobId, setJobId] = useState<string | null>(null);

    const execute = useCallback(async () => {
        setLoading(true);
        setError(null);
        setLogs([]);
        setJobId(null);

        try {
            const { job_id } = await runPipelineStep(stepName);
            setJobId(job_id);

            // Poll for completion
            const pollInterval = setInterval(async () => {
                try {
                    const status = await getPipelineStatus(job_id);

                    if (status.logs) {
                        setLogs(status.logs);
                    }

                    if (status.status === 'completed') {
                        clearInterval(pollInterval);
                        setCompleted(true);
                        setLoading(false);
                        onComplete?.();
                    } else if (status.status === 'failed') {
                        clearInterval(pollInterval);
                        setError(status.error_message || 'Step failed');
                        setLoading(false);
                    }
                } catch (err) {
                    clearInterval(pollInterval);
                    console.error('Poll failed', err);
                }
            }, 1000);

        } catch (err: any) {
            console.error("Step execution failed", err);
            let msg = err.message || 'Failed to start step';
            if (err.response?.data?.detail) {
                msg = err.response.data.detail;
            }
            setError(msg);
            setLoading(false);
        }
    }, [stepName, onComplete]);

    return { execute, loading, error, completed, logs, jobId };
}

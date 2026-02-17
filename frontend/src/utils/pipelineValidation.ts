/**
 * Pipeline Data Validation and Safe Access Utilities
 */

export interface ValidationResult {
    valid: boolean;
    reason: string | null;
}

export function validatePipeline(pipeline: any): ValidationResult {
    if (!pipeline) {
        return { valid: false, reason: "Pipeline data is null or undefined" };
    }
    if (typeof pipeline !== 'object') {
        return { valid: false, reason: "Pipeline data is not an object" };
    }

    // Adjusted check: 'analysis' might be optional depending on state, 
    // but if we are in dashboard, we usually expect meaningful data.
    // The specific requirement was:
    // if (!pipeline.analysis) return { valid: false, reason: "analysis missing" }
    // if (!Array.isArray(pipeline.analysis.steps)) return { valid: false, reason: "steps invalid" }

    // However, the pipeline object structure might vary. 
    // Based on user prompt requirements:
    if (!pipeline.analysis) {
        return { valid: false, reason: "analysis missing" };
    }
    if (!Array.isArray(pipeline.analysis.steps)) {
        return { valid: false, reason: "steps invalid (not an array)" };
    }

    return { valid: true, reason: null };
}

export function safeArray<T>(value: any): T[] {
    return Array.isArray(value) ? value : [];
}

/**
 * Returns a safe pipeline object structure even if input is malformed.
 * Useful for default values in contexts or hooks.
 */
export function safePipelineAccess(pipeline: any) {
    const defaultStructure = {
        analysis: {
            steps: []
        },
        id: "unknown",
        status: "unknown",
        // Add other core fields as needed
    };

    if (!pipeline) return defaultStructure;

    return {
        ...defaultStructure,
        ...pipeline,
        analysis: {
            ...defaultStructure.analysis,
            ...(pipeline.analysis || {}),
            steps: safeArray(pipeline.analysis?.steps)
        }
    };
}

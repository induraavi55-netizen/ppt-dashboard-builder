import React, { createContext, useContext, useEffect, useState } from "react";
import {
    DEFAULT_PIPELINE_CONFIG,
    normalizePipelineConfig,
    type PipelineConfig
} from "./pipelineConfigSchema";
import { getPipelineConfig } from "../api";

// Create context with default
const PipelineConfigContext = createContext<PipelineConfig>(DEFAULT_PIPELINE_CONFIG);

// Mutable context for updates (optional, if we want to support updates via context)
// For now, adhering to user request for immutable safe PROVISION. 
// Updates will still go through API but the provider will need a refresh mechanism ideally.
// But the user prompt specified: "Components must NEVER fetch... individually"
// We'll stick to the requested simple provider pattern.

export function PipelineConfigProvider({ children }: { children: React.ReactNode }) {

    const [config, setConfig] = useState<PipelineConfig>(DEFAULT_PIPELINE_CONFIG);
    const [loaded, setLoaded] = useState(false);

    useEffect(() => {
        let mounted = true;

        async function loadConfig() {
            try {
                const response = await getPipelineConfig();
                const safeConfig = normalizePipelineConfig(response);
                if (mounted) {
                    setConfig(safeConfig);
                    console.log("PipelineConfig loaded:", safeConfig);
                    // Debug global
                    if (typeof window !== "undefined") {
                        (window as any).pipelineConfigDebug = safeConfig;
                    }
                }
            } catch (err) {
                console.error("Failed to load pipeline config, using defaults", err);
                if (mounted) setConfig(DEFAULT_PIPELINE_CONFIG);
            } finally {
                if (mounted) setLoaded(true);
            }
        }

        loadConfig();

        return () => { mounted = false; };
    }, []);

    if (!loaded) {
        return (
            <div className="flex h-screen w-full items-center justify-center bg-gray-50">
                <div className="flex flex-col items-center gap-4">
                    <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600"></div>
                    <p className="text-gray-500 font-medium">Loading System Configuration...</p>
                </div>
            </div>
        );
    }

    return (
        <PipelineConfigContext.Provider value={config}>
            {children}
        </PipelineConfigContext.Provider>
    );
}

export function usePipelineConfig(): PipelineConfig {
    return useContext(PipelineConfigContext);
}

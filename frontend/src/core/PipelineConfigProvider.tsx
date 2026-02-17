import React, { createContext, useContext, useEffect, useState } from "react";
import {
    DEFAULT_PIPELINE_CONFIG,
    normalizePipelineConfig,
    type PipelineConfig
} from "./pipelineConfigSchema";
import { getPipelineConfig } from "../api";

const PipelineConfigContext = createContext<PipelineConfig>(DEFAULT_PIPELINE_CONFIG);

export function PipelineConfigProvider({ children }: { children: React.ReactNode }) {

    const [config, setConfig] = useState<PipelineConfig>(DEFAULT_PIPELINE_CONFIG);

    useEffect(() => {

        let mounted = true;

        async function loadConfig() {

            try {

                const response = await getPipelineConfig();

                const safeConfig = normalizePipelineConfig(response);

                if (mounted) {

                    setConfig(safeConfig);

                    console.log("PipelineConfig loaded:", safeConfig);

                    if (typeof window !== "undefined") {
                        (window as any).pipelineConfigDebug = safeConfig;
                    }
                }

            } catch (err) {

                console.error("Failed to load pipeline config, using defaults", err);

                if (mounted) {
                    setConfig(DEFAULT_PIPELINE_CONFIG);
                }
            }
        }

        loadConfig();

        return () => {
            mounted = false;
        };

    }, []);

    return (
        <PipelineConfigContext.Provider value={config}>
            {children}
        </PipelineConfigContext.Provider>
    );
}

export function usePipelineConfig(): PipelineConfig {
    return useContext(PipelineConfigContext);
}

import { useMemo } from "react";
import { type PipelineConfig } from "../config/defaultPipelineConfig";
import { normalizePipelineConfig } from "../utils/normalizePipelineConfig";

export function useSafePipelineConfig(config: any): PipelineConfig {
    return useMemo(() => {
        return normalizePipelineConfig(config);
    }, [config]);
}

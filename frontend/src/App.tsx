import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import UploadPage from "./pages/UploadPage";
import DashboardPage from "./pages/DashboardPage";
import AnalysisPipelinePage from "./pages/AnalysisPipelinePage";
import { ErrorBoundary } from "./components/common/ErrorBoundary";
import { useEffect } from "react";

const queryClient = new QueryClient();

// Add global debug object type
declare global {
  interface Window {
    pipelineDebug: any;
  }
}

import { PipelineConfigProvider } from "./core/PipelineConfigProvider";

function App() {
  // Initialize debug object
  useEffect(() => {
    if (typeof window !== "undefined") {
      window.pipelineDebug = "Pipeline Debug Initialized";
    }
  }, []);

  return (
    <PipelineConfigProvider>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <div className="min-h-screen bg-gray-50 text-gray-900 font-sans">
            <ErrorBoundary>
              <Routes>
                <Route path="/" element={<AnalysisPipelinePage />} />
                <Route path="/upload" element={<UploadPage />} />
                <Route path="/dashboard" element={<DashboardPage />} />
              </Routes>
            </ErrorBoundary>
          </div>
        </BrowserRouter>
      </QueryClientProvider>
    </PipelineConfigProvider>
  );
}

export default App;

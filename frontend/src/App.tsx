import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes, Navigate } from "react-router-dom";
import UploadPage from "./pages/UploadPage";
import DashboardPage from "./pages/DashboardPage";
import AnalysisPipelinePage from "./pages/AnalysisPipelinePage";
import { ErrorBoundary } from "./components/common/ErrorBoundary";
import { useEffect } from "react";
import { PipelineConfigProvider } from "./core/PipelineConfigProvider";

const queryClient = new QueryClient();

declare global {
  interface Window {
    pipelineDebug: any;
  }
}

function App() {

  useEffect(() => {

    if (typeof window !== "undefined") {

      window.pipelineDebug = "Pipeline Debug Initialized";

    }

  }, []);

  return (

    <PipelineConfigProvider>

      <QueryClientProvider client={queryClient}>

        <BrowserRouter>

          <ErrorBoundary>

            <div className="min-h-screen bg-gray-50 text-gray-900 font-sans">

              <Routes>

                <Route path="/" element={<AnalysisPipelinePage />} />

                <Route path="/upload" element={<UploadPage />} />

                <Route path="/dashboard" element={<DashboardPage />} />

                <Route path="*" element={<Navigate to="/" replace />} />

              </Routes>

            </div>

          </ErrorBoundary>

        </BrowserRouter>

      </QueryClientProvider>

    </PipelineConfigProvider>

  );
}

export default App;

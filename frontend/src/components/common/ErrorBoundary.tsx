import React from 'react';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';

interface Props {
    children: React.ReactNode;
    fallback?: React.ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
    errorInfo: React.ErrorInfo | null;
}

export class ErrorBoundary extends React.Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false, error: null, errorInfo: null };
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error, errorInfo: null };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        console.error("Uncaught error in ErrorBoundary:", error, errorInfo);
        this.setState({ errorInfo });
        // TODO: Send to backend logging endpoint if available
    }

    handleReload = () => {
        window.location.reload();
    };

    handleHome = () => {
        window.location.href = '/';
    };

    render() {
        if (this.state.hasError) {
            if (this.props.fallback) {
                return this.props.fallback;
            }

            return (
                <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4 font-sans">
                    <div className="max-w-xl w-full bg-white p-8 rounded-lg shadow-xl border border-red-100">
                        <div className="flex flex-col items-center text-center">
                            <div className="bg-red-50 p-3 rounded-full mb-4">
                                <AlertCircle className="h-10 w-10 text-red-500" />
                            </div>

                            <h1 className="text-2xl font-bold text-gray-900 mb-2">
                                Something went wrong
                            </h1>

                            <p className="text-gray-500 mb-6">
                                The application encountered an unexpected error and cannot continue.
                            </p>

                            <div className="w-full text-left bg-red-50 p-4 rounded-md border border-red-200 mb-6 overflow-auto max-h-48">
                                <p className="text-sm font-semibold text-red-800 mb-1">Error Details:</p>
                                <code className="text-xs text-red-700 block whitespace-pre-wrap font-mono">
                                    {this.state.error?.toString() || "Unknown Error"}
                                </code>
                                {this.state.errorInfo && (
                                    <details className="mt-2 text-xs text-red-600 cursor-pointer">
                                        <summary>Stack Trace</summary>
                                        <pre className="mt-2 whitespace-pre-wrap">
                                            {this.state.errorInfo.componentStack}
                                        </pre>
                                    </details>
                                )}
                            </div>

                            <div className="flex gap-4 w-full">
                                <button
                                    onClick={this.handleHome}
                                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
                                >
                                    <Home size={18} />
                                    Return Home
                                </button>
                                <button
                                    onClick={this.handleReload}
                                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                                >
                                    <RefreshCw size={18} />
                                    Reload Page
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

import { useEffect, useRef } from 'react';
import { Terminal } from 'lucide-react';

interface Props {
    logs: string[];
    className?: string;
}

export function LogViewer({ logs, className = "" }: Props) {
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    if (!logs || logs.length === 0) {
        return null;
    }

    return (
        <div className={`mt-4 border border-gray-800 rounded-md overflow-hidden bg-[#1e1e1e] text-gray-300 font-mono text-sm ${className}`}>
            <div className="flex items-center gap-2 px-4 py-2 bg-[#2d2d2d] border-b border-gray-700">
                <Terminal size={14} className="text-gray-400" />
                <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Execution Logs</span>
            </div>
            <div
                ref={scrollRef}
                className="max-h-64 overflow-y-auto p-4 space-y-1"
            >
                {logs.map((log, i) => (
                    <div key={i} className="whitespace-pre-wrap break-all">
                        {log}
                    </div>
                ))}
            </div>
        </div>
    );
}

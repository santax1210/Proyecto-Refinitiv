import { createContext, useContext, useState, useCallback, useRef } from 'react';

const ToastCtx = createContext(() => {});

const CFG = {
    success: { bg: '#F0FDF4', border: '#86EFAC', text: '#166534', icon: '#22C55E' },
    error:   { bg: '#FEF2F2', border: '#FCA5A5', text: '#991B1B', icon: '#EF4444' },
    warning: { bg: '#FFFBEB', border: '#FCD34D', text: '#92400E', icon: '#F59E0B' },
    info:    { bg: '#EFF6FF', border: '#93C5FD', text: '#1E40AF', icon: '#3B82F6' },
};

function ToastIcon({ type }) {
    const color = CFG[type]?.icon || CFG.info.icon;
    return (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color}
            strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
            style={{ flexShrink: 0, marginTop: 1 }}>
            {type === 'success' && <polyline points="20 6 9 17 4 12" />}
            {type === 'error'   && <><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></>}
            {type === 'warning' && <><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></>}
            {type === 'info'    && <><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></>}
        </svg>
    );
}

function ToastItem({ toast, onDismiss }) {
    const c = CFG[toast.type] || CFG.info;
    return (
        <div
            onClick={() => onDismiss(toast.id)}
            style={{
                display: 'flex', alignItems: 'flex-start', gap: 10,
                padding: '12px 14px', maxWidth: 360, minWidth: 260,
                backgroundColor: c.bg, border: `1px solid ${c.border}`,
                borderRadius: 12, boxShadow: '0 8px 24px rgba(0,0,0,0.10)',
                cursor: 'pointer',
                animation: toast.exiting
                    ? 'toastOut 0.3s cubic-bezier(0.4,0,1,1) forwards'
                    : 'toastIn 0.35s cubic-bezier(0.22,1,0.36,1) forwards',
            }}
        >
            <ToastIcon type={toast.type} />
            <p style={{ margin: 0, fontSize: 13, fontWeight: 600, color: c.text, flex: 1, lineHeight: 1.4 }}>
                {toast.message}
            </p>
            <button
                onClick={e => { e.stopPropagation(); onDismiss(toast.id); }}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: c.text, opacity: 0.45, padding: '0 0 0 6px', fontSize: 17, lineHeight: 1, flexShrink: 0 }}
            >×</button>
        </div>
    );
}

export function ToastProvider({ children }) {
    const [toasts, setToasts] = useState([]);
    const idRef = useRef(0);

    const addToast = useCallback(({ message, type = 'info', duration = 4000 }) => {
        const id = ++idRef.current;
        setToasts(prev => [...prev, { id, message, type, exiting: false }]);
        setTimeout(() => {
            setToasts(prev => prev.map(t => t.id === id ? { ...t, exiting: true } : t));
            setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 350);
        }, duration);
    }, []);

    const dismiss = useCallback((id) => {
        setToasts(prev => prev.map(t => t.id === id ? { ...t, exiting: true } : t));
        setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 350);
    }, []);

    return (
        <ToastCtx.Provider value={addToast}>
            {children}
            <div style={{
                position: 'fixed', top: 20, right: 20, zIndex: 9999,
                display: 'flex', flexDirection: 'column', gap: 8,
                pointerEvents: 'none',
            }}>
                {toasts.map(t => (
                    <div key={t.id} style={{ pointerEvents: 'auto' }}>
                        <ToastItem toast={t} onDismiss={dismiss} />
                    </div>
                ))}
            </div>
        </ToastCtx.Provider>
    );
}

export function useToast() {
    return useContext(ToastCtx);
}

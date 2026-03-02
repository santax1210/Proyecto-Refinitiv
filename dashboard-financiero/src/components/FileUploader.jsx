import { useState, useRef, useCallback } from 'react';

/* ── Paleta coherente con el dashboard ── */
const TEAL = '#299D91';
const BORDER = '#DDE3E6';
const BG_CARD = '#FFFFFF';
const TEXT_PRI = '#191919';
const TEXT_SEC = '#71717A';
const TEXT_DIM = '#9F9F9F';

/* ══ Ícono de documento ══ */
function DocIcon() {
    return (
        <div style={{ width: 48, height: 48, borderRadius: 12, backgroundColor: '#F3F6F8', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#299D91" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
            </svg>
        </div>
    );
}

/* ══ Fila de archivo ══ */
function FileRow({ id, name, size, progress, onRemove }) {
    const done = progress >= 100;
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '12px 16px', borderRadius: 12, backgroundColor: '#F8FAFB', border: `1px solid ${BORDER}` }}>
            <div style={{ width: 36, height: 36, borderRadius: 8, backgroundColor: '#EBF7F6', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                </svg>
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ margin: 0, fontSize: 13, fontWeight: 600, color: TEXT_PRI, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{name}</p>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
                    <div style={{ flex: 1, height: 4, borderRadius: 2, backgroundColor: '#E8EAED', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${progress}%`, backgroundColor: TEAL, borderRadius: 2, transition: 'width 0.2s' }} />
                    </div>
                    <span style={{ fontSize: 11, color: done ? TEAL : TEXT_DIM, fontWeight: 600, flexShrink: 0 }}>
                        {done ? '✓ Listo' : `${progress}%`}
                    </span>
                </div>
                <p style={{ margin: '3px 0 0', fontSize: 11, color: TEXT_DIM }}>{size}</p>
            </div>
            <button
                onClick={() => onRemove(id)}
                style={{ width: 28, height: 28, borderRadius: 7, border: `1px solid ${BORDER}`, backgroundColor: BG_CARD, color: TEXT_DIM, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, transition: 'all 0.15s' }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = '#FCA5A5'; e.currentTarget.style.color = '#EF4444'; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = BORDER; e.currentTarget.style.color = TEXT_DIM; }}
            >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                    <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                </svg>
            </button>
        </div>
    );
}

/* ══ FileUploader Principal ══ */
export default function FileUploader({ onAttach }) {
    const [files, setFiles] = useState([]);
    const [dragging, setDragging] = useState(false);
    const inputRef = useRef(null);

    const simulateProgress = useCallback((id) => {
        let p = 0;
        const iv = setInterval(() => {
            p += Math.floor(Math.random() * 20) + 8;
            if (p >= 100) { p = 100; clearInterval(iv); }
            setFiles(prev => prev.map(f => f.id === id ? { ...f, progress: p } : f));
        }, 180);
    }, []);

    const addFiles = useCallback((rawFiles) => {
        const entries = Array.from(rawFiles).map(f => ({
            id: Math.random().toString(36).slice(2),
            name: f.name,
            size: (f.size / (1024 * 1024)).toFixed(2) + ' MB',
            progress: 0,
        }));
        setFiles(prev => [...prev, ...entries]);
        entries.forEach(e => simulateProgress(e.id));
    }, [simulateProgress]);

    const handleDrop = (e) => {
        e.preventDefault(); setDragging(false);
        if (e.dataTransfer.files.length) addFiles(e.dataTransfer.files);
    };

    const removeFile = (id) => setFiles(prev => prev.filter(f => f.id !== id));
    const attachable = files.filter(f => f.progress >= 100);

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {/* ── Zona de Drag & Drop ── */}
            <div
                onDragOver={e => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
                onClick={() => inputRef.current.click()}
                style={{
                    display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                    gap: 10, padding: '20px 20px',
                    borderRadius: 16, cursor: 'pointer',
                    border: `1.5px dashed ${dragging ? TEAL : '#C8D0D8'}`,
                    backgroundColor: dragging ? '#EBF7F6' : '#FAFBFC',
                    transition: 'all 0.15s',
                }}
            >
                <DocIcon />
                <div style={{ textAlign: 'center' }}>
                    <p style={{ margin: 0, fontSize: 14, fontWeight: 700, color: TEXT_PRI }}>
                        Arrastrá tu archivo aquí
                    </p>
                    <p style={{ margin: '4px 0 0', fontSize: 12, color: TEXT_SEC }}>
                        CSV, XLSX, XLS — hasta 50 MB
                    </p>
                </div>
                <button
                    onClick={e => { e.stopPropagation(); inputRef.current.click(); }}
                    style={{
                        marginTop: 4, padding: '7px 20px', borderRadius: 8,
                        border: `1px solid ${BORDER}`, backgroundColor: BG_CARD,
                        fontSize: 12, fontWeight: 600, color: TEXT_SEC, cursor: 'pointer', transition: 'all 0.15s',
                    }}
                    onMouseEnter={e => { e.currentTarget.style.borderColor = TEAL; e.currentTarget.style.color = TEAL; }}
                    onMouseLeave={e => { e.currentTarget.style.borderColor = BORDER; e.currentTarget.style.color = TEXT_SEC; }}
                >
                    Seleccionar archivo
                </button>
                <input ref={inputRef} type="file" multiple style={{ display: 'none' }}
                    onChange={e => { if (e.target.files.length) addFiles(e.target.files); }} />
            </div>

            {/* ── Lista de archivos ── */}
            {files.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    <p style={{ margin: 0, fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: TEXT_DIM }}>
                        Archivos ({files.length})
                    </p>
                    {files.map(f => <FileRow key={f.id} {...f} onRemove={removeFile} />)}
                </div>
            )}

            {/* ── Botón Adjuntar ── */}
            <button
                onClick={() => onAttach && onAttach(attachable)}
                disabled={attachable.length === 0}
                style={{
                    width: '100%', padding: '12px',
                    borderRadius: 12, border: 'none',
                    fontSize: 14, fontWeight: 700,
                    backgroundColor: attachable.length > 0 ? TEAL : '#E8EAED',
                    color: attachable.length > 0 ? '#FFFFFF' : TEXT_DIM,
                    cursor: attachable.length > 0 ? 'pointer' : 'not-allowed',
                    transition: 'background-color 0.15s',
                }}
                onMouseEnter={e => { if (attachable.length > 0) e.currentTarget.style.backgroundColor = '#227d73'; }}
                onMouseLeave={e => { if (attachable.length > 0) e.currentTarget.style.backgroundColor = TEAL; }}
            >
                {attachable.length > 0 ? `Procesar ${attachable.length} archivo${attachable.length > 1 ? 's' : ''}` : 'Adjuntar archivo'}
            </button>
        </div>
    );
}

import { useRef, useState } from 'react';
import { useApp } from '../context/AppContext';
import { useToast } from '../context/ToastContext';

const TEAL = '#299D91';
const BORDER = '#DDE3E6';
const CLASIFICACIONES = ['Moneda', 'Región', 'Industria'];

const SLOTS = [
    { key: 'posiciones',          label: 'Posiciones',      desc: 'archivo de posiciones' },
    { key: 'instruments',         label: 'Instrumentos',    desc: 'maestro de instrumentos' },
    { key: 'allocations_nuevas',  label: 'Alloc. Nuevas',   desc: 'formato WIDE' },
    { key: 'allocations_antiguas',label: 'Alloc. Antiguas', desc: 'históricas' },
];

/* ── Slot individual de archivo ── */
function FileSlot({ slotKey, label, desc, file, onFile, onClear }) {
    const ref = useRef(null);
    const [dragging, setDragging] = useState(false);
    const filled = !!file;

    const handleDrop = (e) => {
        e.preventDefault();
        setDragging(false);
        const dropped = e.dataTransfer?.files?.[0];
        if (dropped && !filled) onFile(slotKey, dropped);
    };

    return (
        <>
            <input
                ref={ref} type="file" accept=".csv,.xlsx,.xls"
                style={{ display: 'none' }}
                onChange={e => { if (e.target.files[0]) onFile(slotKey, e.target.files[0]); e.target.value = ''; }}
            />
            <div
                onClick={() => !filled && ref.current.click()}
                onDragOver={e => { e.preventDefault(); if (!filled) setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
                className={dragging ? 'drag-over' : ''}
                style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '8px 12px', borderRadius: 10,
                    cursor: filled ? 'default' : dragging ? 'copy' : 'pointer',
                    border: `1.5px ${filled ? 'solid' : dragging ? 'solid' : 'dashed'} ${filled ? TEAL : dragging ? TEAL : '#C8D0D8'}`,
                    backgroundColor: filled ? '#EBF7F6' : dragging ? '#E6F8F5' : '#FAFBFC',
                    transition: 'all 0.15s', minHeight: 52,
                }}
                onMouseEnter={e => { if (!filled && !dragging) { e.currentTarget.style.borderColor = TEAL; e.currentTarget.style.backgroundColor = '#F4FDFC'; } }}
                onMouseLeave={e => { if (!filled && !dragging) { e.currentTarget.style.borderColor = '#C8D0D8'; e.currentTarget.style.backgroundColor = '#FAFBFC'; } }}
            >
                {/* Icono */}
                <div style={{
                    width: 30, height: 30, borderRadius: 8, flexShrink: 0,
                    backgroundColor: filled ? TEAL : '#EEF1F3',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                    {filled
                        ? <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#FFF" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
                        : <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#9F9F9F" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /></svg>
                    }
                </div>

                {/* Texto */}
                <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ margin: 0, fontSize: 11, fontWeight: 700, color: filled ? '#1a7a70' : '#525256', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {filled ? file.name : label}
                    </p>
                    <p style={{ margin: 0, fontSize: 10, color: filled ? TEAL : '#9F9F9F' }}>
                        {filled ? `${label} · ${(file.size / (1024 * 1024)).toFixed(1)} MB` : desc}
                    </p>
                </div>

                {/* Acción */}
                {filled
                    ? <button onClick={e => { e.stopPropagation(); onClear(slotKey); }} style={{ width: 22, height: 22, borderRadius: 6, flexShrink: 0, border: '1px solid rgba(41,157,145,0.3)', backgroundColor: 'rgba(41,157,145,0.1)', color: TEAL, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 15, lineHeight: 1 }}>×</button>
                    : <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#BCBCBC" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></svg>
                }
            </div>
        </>
    );
}


export default function InicioPage() {
    const { clasificacion, setClasificacion, uploadAndProcess, processingState } = useApp();
    const toast = useToast();
    const [slots, setSlots] = useState({});
    const [processing, setProcessing] = useState(false);
    const [error, setError] = useState(null);

    const handleFile  = (key, file) => setSlots(prev => ({ ...prev, [key]: file }));
    const handleClear = (key) => setSlots(prev => { const n = { ...prev }; delete n[key]; return n; });

    const filledCount = Object.keys(slots).length;
    const allReady    = filledCount === SLOTS.length && !!clasificacion;

    const btnLabel = processing
        ? 'Procesando...'
        : !clasificacion
            ? 'Seleccioná un tipo de clasificación'
            : filledCount < SLOTS.length
                ? `Faltan ${SLOTS.length - filledCount} archivo${SLOTS.length - filledCount > 1 ? 's' : ''}`
                : 'Procesar Validación';

    const handleProcess = async () => {
        if (!allReady) return;
        setProcessing(true);
        setError(null);
        try {
            await uploadAndProcess({ ...slots });
            toast({ message: 'Pipeline completado. Revisá los resultados en Validación.', type: 'success', duration: 5000 });
        } catch (err) {
            const msg = err.message || 'Error al procesar archivos';
            setError(msg);
            toast({ message: msg, type: 'error' });
        } finally {
            setProcessing(false);
        }
    };

    return (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', height: '100%', padding: '28px 32px' }}>
            {/* ── Card split-panel ── */}
            <div className="anim-zoom-in" style={{
                display: 'grid', gridTemplateColumns: '260px 1fr',
                width: '100%', maxWidth: 820,
                backgroundColor: '#FFFFFF', borderRadius: 24,
                border: `1px solid ${BORDER}`,
                boxShadow: '0 8px 32px rgba(0,0,0,0.10)',
                overflow: 'hidden', minHeight: 460,
            }}>
                {/* ── Panel izquierdo (branding) ── */}
                <div style={{ background: 'linear-gradient(160deg, #1e6e67 0%, #299D91 55%, #34bfb0 100%)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', padding: '36px 28px' }}>
                    <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 28 }}>
                            <div style={{ width: 36, height: 36, borderRadius: 10, backgroundColor: 'rgba(255,255,255,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12" /></svg>
                            </div>
                            <span style={{ fontSize: 15, fontWeight: 800, color: '#FFFFFF', letterSpacing: '-0.3px' }}>Refinitiv</span>
                        </div>
                        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 800, color: '#FFFFFF', lineHeight: 1.25, letterSpacing: '-0.5px' }}>Validación de Allocations</h1>
                        <p style={{ margin: '12px 0 0', fontSize: 13, color: 'rgba(255,255,255,0.75)', lineHeight: 1.6 }}>
                            Seleccioná el tipo de clasificación y cargá los 4 archivos en cualquier orden. Cuando estén listos, ejecutá el pipeline.
                        </p>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                        {[{ label: 'Procesamiento', value: 'Automático' }, { label: 'Seguridad', value: 'Encriptado' }, { label: 'Reportes', value: 'Tiempo Real' }].map(item => (
                            <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', borderRadius: 10, backgroundColor: 'rgba(255,255,255,0.12)' }}>
                                <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.7)' }}>{item.label}</span>
                                <span style={{ fontSize: 11, fontWeight: 700, color: '#FFFFFF' }}>{item.value}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* ── Panel derecho (upload) ── */}
                <div style={{ display: 'flex', flexDirection: 'column', padding: '28px 28px', gap: 14 }}>

                    {/* Cabecera */}
                    <div>
                        <p style={{ margin: 0, fontSize: 9, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.12em', color: '#9F9F9F' }}>Nuevo Pipeline</p>
                        <h2 style={{ margin: '4px 0 0', fontSize: 16, fontWeight: 700, color: '#191919' }}>Configurar y Procesar</h2>
                    </div>

                    {/* Tipo de clasificación */}
                    {/* Si ya cargaron todos los archivos pero falta la clasificación, resaltar el selector */}
                    <div style={{
                        display: 'flex', flexDirection: 'column', gap: 7,
                        padding: filledCount === SLOTS.length && !clasificacion ? '10px 12px' : '0',
                        borderRadius: filledCount === SLOTS.length && !clasificacion ? 10 : 0,
                        border: filledCount === SLOTS.length && !clasificacion ? `1.5px solid ${TEAL}` : 'none',
                        backgroundColor: filledCount === SLOTS.length && !clasificacion ? '#EBF7F6' : 'transparent',
                        transition: 'all 0.2s',
                    }}>
                        <label style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: filledCount === SLOTS.length && !clasificacion ? TEAL : '#71717A' }}>
                            {filledCount === SLOTS.length && !clasificacion ? '⚠ Seleccioná el tipo de clasificación' : 'Tipo de Clasificación'}
                        </label>
                        <div style={{ display: 'flex', gap: 6 }}>
                            {CLASIFICACIONES.map(c => {
                                const active = clasificacion === c;
                                return (
                                    <button key={c} onClick={() => setClasificacion(active ? '' : c)}
                                        style={{ padding: '5px 12px', borderRadius: 7, fontSize: 11, fontWeight: 600, border: `1px solid ${active ? TEAL : BORDER}`, backgroundColor: active ? '#EBF7F6' : '#FFFFFF', color: active ? TEAL : '#525256', cursor: 'pointer', transition: 'all 0.12s' }}
                                        onMouseEnter={e => { if (!active) { e.currentTarget.style.borderColor = TEAL; e.currentTarget.style.color = TEAL; } }}
                                        onMouseLeave={e => { if (!active) { e.currentTarget.style.borderColor = BORDER; e.currentTarget.style.color = '#525256'; } }}
                                    >{c}</button>
                                );
                            })}
                        </div>
                    </div>

                    {/* Divisor */}
                    <div style={{ height: 1, backgroundColor: '#F0F2F4' }} />

                    {/* Slots de archivo — grid 2×2 */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <label style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#71717A' }}>Archivos</label>
                            <span style={{ fontSize: 10, fontWeight: 700, color: filledCount === SLOTS.length ? TEAL : '#9F9F9F' }}>
                                {filledCount}/{SLOTS.length}
                            </span>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                            {SLOTS.map(s => (
                                <FileSlot
                                    key={s.key} slotKey={s.key} label={s.label} desc={s.desc}
                                    file={slots[s.key] || null} onFile={handleFile} onClear={handleClear}
                                />
                            ))}
                        </div>
                    </div>

                    {/* Error */}
                    {error && (
                        <div style={{ padding: '10px 14px', borderRadius: 10, backgroundColor: '#FEE2E2', border: '1px solid #FCA5A5' }}>
                            <p style={{ margin: 0, fontSize: 12, color: '#991B1B', fontWeight: 600 }}>{error}</p>
                        </div>
                    )}

                    {/* Progreso — se oculta en cuanto el contexto reporta 'completed' */}
                    {processing && processingState.status !== 'completed' && (
                        <div style={{ padding: '10px 14px', borderRadius: 10, backgroundColor: '#F3F6F8', border: `1px solid ${BORDER}` }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 7 }}>
                                <div style={{ width: 13, height: 13, border: '2px solid ' + TEAL, borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite', flexShrink: 0 }} />
                                <p style={{ margin: 0, fontSize: 12, fontWeight: 600, color: '#525256', flex: 1 }}>{processingState.message || 'Procesando...'}</p>
                                <span style={{ fontSize: 10, fontWeight: 700, color: TEAL }}>{processingState.progress || 0}%</span>
                            </div>
                            <div style={{ height: 4, borderRadius: 2, backgroundColor: '#E8EAED', overflow: 'hidden' }}>
                                <div style={{ height: '100%', width: `${Math.max(processingState.progress || 0, 6)}%`, backgroundColor: TEAL, transition: 'width 0.4s ease', borderRadius: 2 }} />
                            </div>
                        </div>
                    )}
                    {/* Éxito — se muestra en cuanto el contexto reporta 'completed' */}
                    {processingState.status === 'completed' && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', borderRadius: 10, backgroundColor: '#F0FDF4', border: '1px solid #86EFAC', animation: 'fadeSlideUp 0.4s ease both' }}>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#22C55E" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                                style={{ flexShrink: 0, animation: 'successPop 0.45s cubic-bezier(0.34,1.5,0.64,1) both' }}>
                                <circle cx="12" cy="12" r="10" />
                                <polyline points="9 12 11 14 15 10" />
                            </svg>
                            <p style={{ margin: 0, fontSize: 12, fontWeight: 600, color: '#166534' }}>Pipeline completado. Revisá los resultados.</p>
                        </div>
                    )}

                    {/* Spacer */}
                    <div style={{ flex: 1 }} />

                    {/* Botón procesar */}
                    <button
                        onClick={(e) => {
                            if (allReady && !processing) {
                                const btn = e.currentTarget;
                                const rect = btn.getBoundingClientRect();
                                const size = Math.max(rect.width, rect.height) * 2;
                                const span = document.createElement('span');
                                span.style.cssText = `width:${size}px;height:${size}px;left:${e.clientX - rect.left - size / 2}px;top:${e.clientY - rect.top - size / 2}px;position:absolute;border-radius:50%;background:rgba(255,255,255,0.28);animation:ripple 0.6s linear;pointer-events:none;`;
                                btn.appendChild(span);
                                setTimeout(() => span.remove(), 700);
                            }
                            handleProcess();
                        }}
                        disabled={!allReady || processing}
                        style={{
                            width: '100%', padding: '11px', borderRadius: 12, border: 'none',
                            fontSize: 13, fontWeight: 700,
                            backgroundColor: allReady && !processing ? TEAL : '#E8EAED',
                            color: allReady && !processing ? '#FFFFFF' : '#9F9F9F',
                            cursor: allReady && !processing ? 'pointer' : 'not-allowed',
                            transition: 'background-color 0.15s',
                            position: 'relative', overflow: 'hidden',
                        }}
                        onMouseEnter={e => { if (allReady && !processing) e.currentTarget.style.backgroundColor = '#227d73'; }}
                        onMouseLeave={e => { if (allReady && !processing) e.currentTarget.style.backgroundColor = TEAL; }}
                    >
                        {btnLabel}
                    </button>
                </div>
            </div>
        </div>
    );
}

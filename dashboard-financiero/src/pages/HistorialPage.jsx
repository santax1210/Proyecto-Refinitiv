import { useState, useEffect, useMemo } from 'react';
import { getHistory, getHistoryDetail, deleteHistoryEntry } from '../services/apiService';
import { useToast } from '../context/ToastContext';

/* ── Tokens de color ── */
const TEAL = '#299D91';
const CLASIF_CFG = {
    moneda: { label: 'Moneda', bg: '#EEF2FF', text: '#6366F1', dot: '#6366F1' },
    region: { label: 'Región', bg: '#EBF7F6', text: '#299D91', dot: '#299D91' },
    sector: { label: 'Industria', bg: '#FFF7ED', text: '#D97706', dot: '#D97706' },
};

function formatDate(iso) {
    if (!iso) return '—';
    const d = new Date(iso);
    return d.toLocaleDateString('es-CL', { day: '2-digit', month: 'short', year: 'numeric' })
        + ' · '
        + d.toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit' });
}

/* ── Pill de clasificación ── */
function ClasifPill({ clasificacion }) {
    const c = CLASIF_CFG[clasificacion] || { label: clasificacion, bg: '#F3F4F6', text: '#6B7280', dot: '#9CA3AF' };
    return (
        <span style={{
            display: 'inline-flex', alignItems: 'center', gap: 5,
            padding: '3px 10px', borderRadius: 999,
            backgroundColor: c.bg, color: c.text,
            fontSize: 11, fontWeight: 600, letterSpacing: '0.02em',
        }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: c.dot, flexShrink: 0 }} />
            {c.label}
        </span>
    );
}

/* ── Métrica individual ── */
function MetricBadge({ label, value, color = '#191919', icon }) {
    return (
        <div style={{
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2,
            minWidth: 56,
        }}>
            <span style={{ fontSize: 20, fontWeight: 800, color, lineHeight: '1.1' }}>{value}</span>
            <span style={{ fontSize: 10, fontWeight: 500, color: '#9F9F9F', textTransform: 'uppercase', letterSpacing: '0.04em', textAlign: 'center' }}>
                {icon} {label}
            </span>
        </div>
    );
}

/* ── Barra de progreso ── */
function ProgressBar({ pct }) {
    return (
        <div style={{ width: '100%', height: 6, borderRadius: 999, backgroundColor: '#F0F0F0', overflow: 'hidden' }}>
            <div style={{
                height: '100%', borderRadius: 999,
                width: `${Math.min(pct, 100)}%`,
                backgroundColor: pct >= 100 ? TEAL : pct > 50 ? '#3B82F6' : '#F59E0B',
                transition: 'width 0.4s ease',
            }} />
        </div>
    );
}

/* ═══════════════════════════════════════════════════════════════
   HistorialPage
   ═══════════════════════════════════════════════════════════════ */
export default function HistorialPage() {
    const toast = useToast();
    const [entries, setEntries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [filterClasif, setFilterClasif] = useState(null);

    // Modal de detalle
    const [detailEntry, setDetailEntry] = useState(null);
    const [detailLoading, setDetailLoading] = useState(false);

    // Confirmación de eliminación
    const [deleteId, setDeleteId] = useState(null);

    /* ── Cargar lista ── */
    useEffect(() => {
        setLoading(true);
        getHistory()
            .then(res => setEntries(res.entries || []))
            .catch(err => {
                console.error(err);
                toast({ message: 'Error al cargar historial', type: 'error' });
            })
            .finally(() => setLoading(false));
    }, []); // eslint-disable-line

    /* ── Filtrado ── */
    const filtered = useMemo(() => {
        let list = entries;
        if (filterClasif) list = list.filter(e => e.clasificacion === filterClasif);
        if (search) {
            const q = search.toLowerCase();
            list = list.filter(e =>
                (e.label || '').toLowerCase().includes(q) ||
                (e.clasificacion || '').toLowerCase().includes(q) ||
                (e.timestamp || '').toLowerCase().includes(q)
            );
        }
        return list;
    }, [entries, search, filterClasif]);

    /* ── Abrir detalle ── */
    const openDetail = async (id) => {
        setDetailLoading(true);
        try {
            const res = await getHistoryDetail(id);
            setDetailEntry(res.entry);
        } catch (err) {
            toast({ message: 'Error al cargar detalle', type: 'error' });
        } finally {
            setDetailLoading(false);
        }
    };

    /* ── Eliminar ── */
    const confirmDelete = async () => {
        if (!deleteId) return;
        try {
            await deleteHistoryEntry(deleteId);
            setEntries(prev => prev.filter(e => e.id !== deleteId));
            toast({ message: 'Entrada eliminada del historial', type: 'success' });
            if (detailEntry?.id === deleteId) setDetailEntry(null);
        } catch (err) {
            toast({ message: 'Error al eliminar', type: 'error' });
        } finally {
            setDeleteId(null);
        }
    };

    /* ═══════════════ RENDER ═══════════════ */
    return (
        <div className="anim-fade-slide" style={{ display: 'flex', flexDirection: 'column', gap: 16, padding: '24px 28px', width: '100%', maxWidth: '1400px', margin: '0 auto' }}>

            {/* ── Header ── */}
            <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
                <div>
                    <h1 style={{ margin: 0, fontSize: 22, fontWeight: 800, color: '#191919', letterSpacing: '-0.3px' }}>
                        Historial de Validaciones
                    </h1>
                    <p style={{ margin: '4px 0 0', fontSize: 13, color: '#71717A' }}>
                        Registro de todas las sesiones de validación guardadas
                    </p>
                </div>
                <span style={{ fontSize: 12, fontWeight: 600, color: '#9F9F9F' }}>
                    {filtered.length} registro{filtered.length !== 1 ? 's' : ''}
                </span>
            </div>

            {/* ── Toolbar: Search + Filtro ── */}
            <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                {/* Search */}
                <div style={{ position: 'relative', flex: 1, minWidth: 200 }}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#9F9F9F" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                        style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }}>
                        <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
                    </svg>
                    <input
                        type="text"
                        placeholder="Buscar por etiqueta o fecha..."
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                        style={{
                            width: '100%', padding: '9px 12px 9px 34px',
                            border: '1.5px solid #E5E7EB', borderRadius: 10,
                            fontSize: 13, outline: 'none', backgroundColor: '#FFFFFF',
                            transition: 'border-color 0.15s',
                        }}
                        onFocus={e => e.target.style.borderColor = TEAL}
                        onBlur={e => e.target.style.borderColor = '#E5E7EB'}
                    />
                </div>

                {/* Filtros clasificación */}
                {['moneda', 'region', 'sector'].map(key => {
                    const isActive = filterClasif === key;
                    const cfg = CLASIF_CFG[key];
                    return (
                        <button key={key} onClick={() => setFilterClasif(isActive ? null : key)}
                            style={{
                                padding: '7px 14px', borderRadius: 20,
                                border: `1.5px solid ${isActive ? cfg.dot : '#E5E7EB'}`,
                                backgroundColor: isActive ? cfg.bg : '#FFFFFF',
                                color: isActive ? cfg.text : '#71717A',
                                fontSize: 12, fontWeight: 600, cursor: 'pointer',
                                transition: 'all 0.15s',
                            }}
                        >
                            {cfg.label}
                        </button>
                    );
                })}
            </div>

            {/* ── Loading skeleton ── */}
            {loading && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 16 }}>
                    {[1, 2, 3].map(i => (
                        <div key={i} className="skeleton" style={{ height: 180, borderRadius: 16 }} />
                    ))}
                </div>
            )}

            {/* ── Empty state ── */}
            {!loading && filtered.length === 0 && (
                <div style={{
                    display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                    padding: '60px 20px', backgroundColor: '#FFFFFF', borderRadius: 16,
                    border: '1px solid #DDE3E6', gap: 16,
                }}>
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#9F9F9F" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
                    </svg>
                    <div style={{ textAlign: 'center' }}>
                        <p style={{ fontSize: 16, fontWeight: 700, color: '#191919', margin: 0 }}>
                            {entries.length === 0 ? 'Aún no hay validaciones guardadas' : 'Sin resultados'}
                        </p>
                        <p style={{ fontSize: 13, color: '#71717A', margin: '8px 0 0' }}>
                            {entries.length === 0
                                ? 'Cuando guardes una validación desde la página de validación, aparecerá aquí.'
                                : 'Probá con otro filtro o término de búsqueda.'}
                        </p>
                    </div>
                </div>
            )}

            {/* ── Grid de tarjetas ── */}
            {!loading && filtered.length > 0 && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 16 }}>
                    {filtered.map(entry => {
                        const m = entry.metrics || {};
                        return (
                            <div key={entry.id}
                                onClick={() => openDetail(entry.id)}
                                style={{
                                    backgroundColor: '#FFFFFF', borderRadius: 16,
                                    border: '1px solid #DDE3E6',
                                    padding: '20px 24px',
                                    cursor: 'pointer',
                                    transition: 'box-shadow 0.2s, transform 0.15s',
                                    display: 'flex', flexDirection: 'column', gap: 14,
                                }}
                                onMouseEnter={e => { e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.08)'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
                                onMouseLeave={e => { e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.transform = 'none'; }}
                            >
                                {/* Header de tarjeta */}
                                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
                                    <div style={{ flex: 1, minWidth: 0 }}>
                                        <p style={{ margin: 0, fontSize: 15, fontWeight: 700, color: '#191919', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                            {entry.label || 'Sin etiqueta'}
                                        </p>
                                        <p style={{ margin: '3px 0 0', fontSize: 11, color: '#9F9F9F', fontWeight: 500 }}>
                                            {formatDate(entry.timestamp)}
                                        </p>
                                    </div>
                                    <ClasifPill clasificacion={entry.clasificacion} />
                                </div>

                                {/* Progreso */}
                                <div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                        <span style={{ fontSize: 11, fontWeight: 600, color: '#525256' }}>Avance de revisión</span>
                                        <span style={{ fontSize: 11, fontWeight: 700, color: TEAL }}>{m.pct_avance ?? 0}%</span>
                                    </div>
                                    <ProgressBar pct={m.pct_avance ?? 0} />
                                </div>

                                {/* Métricas */}
                                <div style={{
                                    display: 'flex', justifyContent: 'space-around',
                                    padding: '10px 0 2px',
                                    borderTop: '1px solid #F0F0F0',
                                }}>
                                    <MetricBadge label="Total" value={m.total ?? 0} color="#191919" />
                                    <MetricBadge label="Validados" value={m.validados ?? 0} color={TEAL} />
                                    <MetricBadge label="Rechazados" value={m.rechazados ?? 0} color="#D94A38" />
                                    <MetricBadge label="Pendientes" value={m.pendientes ?? 0} color="#F59E0B" />
                                </div>

                                {/* Alta variación badge */}
                                {(m.alta_variacion ?? 0) > 0 && (
                                    <div style={{
                                        display: 'inline-flex', alignItems: 'center', gap: 5,
                                        padding: '4px 10px', borderRadius: 8,
                                        backgroundColor: '#FFF7ED', color: '#D97706',
                                        fontSize: 11, fontWeight: 600, alignSelf: 'flex-start',
                                    }}>
                                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                                            <line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" />
                                        </svg>
                                        {m.alta_variacion} con alta variación
                                    </div>
                                )}

                                {/* Botón eliminar */}
                                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                                    <button
                                        onClick={(e) => { e.stopPropagation(); setDeleteId(entry.id); }}
                                        style={{
                                            background: 'none', border: 'none', cursor: 'pointer',
                                            color: '#C4C4C4', fontSize: 11, fontWeight: 500,
                                            padding: '4px 8px', borderRadius: 6,
                                            transition: 'color 0.15s, background-color 0.15s',
                                        }}
                                        onMouseEnter={e => { e.currentTarget.style.color = '#D94A38'; e.currentTarget.style.backgroundColor = '#FFF0EE'; }}
                                        onMouseLeave={e => { e.currentTarget.style.color = '#C4C4C4'; e.currentTarget.style.backgroundColor = 'transparent'; }}
                                    >
                                        Eliminar
                                    </button>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* ════════════════════════════════════════════════════════════ */}
            {/* MODAL: Confirmación de eliminación                         */}
            {/* ════════════════════════════════════════════════════════════ */}
            {deleteId && (
                <div onClick={() => setDeleteId(null)}
                    style={{ position: 'fixed', inset: 0, zIndex: 300, backgroundColor: 'rgba(0,0,0,0.35)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <div onClick={e => e.stopPropagation()}
                        style={{ backgroundColor: '#FFFFFF', borderRadius: 16, padding: '28px 32px', width: 400, maxWidth: '92vw', boxShadow: '0 20px 40px rgba(0,0,0,0.18)' }}>
                        <h3 style={{ margin: '0 0 8px', fontSize: 16, fontWeight: 700, color: '#191919' }}>¿Eliminar esta validación?</h3>
                        <p style={{ margin: '0 0 20px', fontSize: 13, color: '#71717A' }}>
                            Esta acción no se puede deshacer. Los datos guardados se perderán permanentemente.
                        </p>
                        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                            <button onClick={() => setDeleteId(null)}
                                style={{ padding: '8px 18px', borderRadius: 10, border: '1.5px solid #E5E7EB', backgroundColor: '#FFFFFF', color: '#525256', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>
                                Cancelar
                            </button>
                            <button onClick={confirmDelete}
                                style={{ padding: '8px 18px', borderRadius: 10, border: 'none', backgroundColor: '#D94A38', color: '#FFFFFF', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>
                                Eliminar
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* ════════════════════════════════════════════════════════════ */}
            {/* MODAL: Detalle de validación                               */}
            {/* ════════════════════════════════════════════════════════════ */}
            {(detailEntry || detailLoading) && (
                <div onClick={() => { setDetailEntry(null); setDetailLoading(false); }}
                    style={{ position: 'fixed', inset: 0, zIndex: 200, backgroundColor: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
                    <div onClick={e => e.stopPropagation()}
                        style={{
                            backgroundColor: '#FFFFFF', borderRadius: 18,
                            width: '100%', maxWidth: 960, maxHeight: '85vh',
                            display: 'flex', flexDirection: 'column',
                            boxShadow: '0 24px 48px rgba(0,0,0,0.2)',
                            overflow: 'hidden',
                        }}>
                        {detailLoading ? (
                            <div style={{ padding: 60, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                <div className="skeleton" style={{ width: '80%', height: 200, borderRadius: 12 }} />
                            </div>
                        ) : detailEntry && (
                            <>
                                {/* Header del modal */}
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '20px 28px', borderBottom: '1px solid #F0F0F0' }}>
                                    <div style={{ flex: 1, minWidth: 0 }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 2 }}>
                                            <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800, color: '#191919' }}>{detailEntry.label}</h2>
                                            <ClasifPill clasificacion={detailEntry.clasificacion} />
                                        </div>
                                        <p style={{ margin: 0, fontSize: 12, color: '#9F9F9F' }}>{formatDate(detailEntry.timestamp)}</p>
                                    </div>
                                    <button onClick={() => setDetailEntry(null)}
                                        style={{ width: 32, height: 32, borderRadius: 8, border: 'none', backgroundColor: '#F3F4F6', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#71717A', flexShrink: 0 }}>
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                                        </svg>
                                    </button>
                                </div>

                                {/* Métricas resumen */}
                                <div style={{ display: 'flex', gap: 16, padding: '16px 28px', borderBottom: '1px solid #F0F0F0', flexWrap: 'wrap' }}>
                                    {(() => {
                                        const m = detailEntry.metrics || {};
                                        return (
                                            <>
                                                <MetricBadge label="Total" value={m.total ?? 0} color="#191919" />
                                                <MetricBadge label="Validados" value={m.validados ?? 0} color={TEAL} />
                                                <MetricBadge label="Rechazados" value={m.rechazados ?? 0} color="#D94A38" />
                                                <MetricBadge label="Pendientes" value={m.pendientes ?? 0} color="#F59E0B" />
                                                <MetricBadge label="Alta Var." value={m.alta_variacion ?? 0} color="#D97706" />
                                                <div style={{ flex: 1, minWidth: 120, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                                                    <ProgressBar pct={m.pct_avance ?? 0} />
                                                    <span style={{ fontSize: 10, color: '#9F9F9F', marginTop: 3 }}>{m.pct_avance ?? 0}% revisado</span>
                                                </div>
                                            </>
                                        );
                                    })()}
                                </div>

                                {/* Tabla de instrumentos */}
                                <div style={{ flex: 1, overflowY: 'auto', padding: '0' }}>
                                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                                        <thead>
                                            <tr style={{ backgroundColor: '#FAFAFA', position: 'sticky', top: 0, zIndex: 1 }}>
                                                <th style={{ padding: '10px 16px', textAlign: 'left', fontWeight: 700, color: '#71717A', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.04em' }}>ID</th>
                                                <th style={{ padding: '10px 16px', textAlign: 'left', fontWeight: 700, color: '#71717A', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Instrumento</th>
                                                <th style={{ padding: '10px 16px', textAlign: 'center', fontWeight: 700, color: '#71717A', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Estado</th>
                                                <th style={{ padding: '10px 16px', textAlign: 'center', fontWeight: 700, color: '#71717A', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Variación</th>
                                                <th style={{ padding: '10px 16px', textAlign: 'center', fontWeight: 700, color: '#71717A', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Revisión</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {(detailEntry.instruments || []).map((inst, idx) => {
                                                const rev = detailEntry.revisiones?.[String(inst.ID)] || 'Sin revisar';
                                                const revColor = rev === 'Validado' ? TEAL : rev === 'Rechazado' ? '#D94A38' : '#9F9F9F';
                                                const revBg = rev === 'Validado' ? '#E9F9F7' : rev === 'Rechazado' ? '#FFF0EE' : 'transparent';
                                                const variacion = inst.variacion_balanceados ?? inst.variacion_no_balanceados;
                                                const variacionStr = variacion != null ? `${(parseFloat(variacion) * 100).toFixed(1)}%` : '—';

                                                return (
                                                    <tr key={inst.ID ?? idx}
                                                        style={{ backgroundColor: revBg, borderBottom: '1px solid #F5F5F5', transition: 'background-color 0.1s' }}>
                                                        <td style={{ padding: '9px 16px', fontWeight: 600, color: '#525256' }}>{inst.ID}</td>
                                                        <td style={{ padding: '9px 16px', color: '#191919', fontWeight: 500, maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{inst.Nombre || '—'}</td>
                                                        <td style={{ padding: '9px 16px', textAlign: 'center' }}>
                                                            <span style={{
                                                                display: 'inline-block', padding: '2px 8px', borderRadius: 6,
                                                                backgroundColor: inst.Cambio === 'Balanceado' ? '#EBF7F6' : inst.Cambio === 'Sin datos' ? '#F3F4F6' : '#FFF7ED',
                                                                color: inst.Cambio === 'Balanceado' ? TEAL : inst.Cambio === 'Sin datos' ? '#71717A' : '#D97706',
                                                                fontSize: 11, fontWeight: 600,
                                                            }}>
                                                                {inst.Cambio || '—'}
                                                            </span>
                                                        </td>
                                                        <td style={{ padding: '9px 16px', textAlign: 'center', fontWeight: 600, color: '#525256', fontSize: 12 }}>{variacionStr}</td>
                                                        <td style={{ padding: '9px 16px', textAlign: 'center' }}>
                                                            <span style={{ fontWeight: 700, color: revColor, fontSize: 12 }}>{rev}</span>
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                    {(!detailEntry.instruments || detailEntry.instruments.length === 0) && (
                                        <p style={{ padding: 32, textAlign: 'center', color: '#9F9F9F', fontSize: 13 }}>
                                            No se guardaron instrumentos en esta entrada.
                                        </p>
                                    )}
                                </div>
                            </>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

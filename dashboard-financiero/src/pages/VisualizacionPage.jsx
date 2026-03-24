import { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { useToast } from '../context/ToastContext';
import { getInstrumentDetail } from '../services/apiService';

/* ── Paleta ── */
const TEAL = '#299D91';
const PURPLE = '#6366F1';
const AMBER = '#F0A050';
const RED = '#E05252';
const SLATE = '#64748B';

const CLASE_COLORS = {
    // Monedas
    'USD': TEAL, 'EUR': PURPLE, 'CLP': AMBER, 'JPY': '#06B6D4',
    'GBP': '#8B5CF6', 'HKD': '#EC4899', 'BRL': '#F97316',
    'CNY': '#14B8A6', 'TWD': '#A78BFA', 'INR': '#FB923C',
    'CHF': '#84CC16', 'KRW': '#F43F5E', 'AUD': '#10B981',
    'CAD': '#EF4444', 'SEK': '#7C3AED', 'NOK': '#3B82F6',
    'MXN': '#DC2626', 'ZAR': '#D97706', 'SGD': '#0369A1',
    // Regiones
    'Chile': TEAL, 'Norteamerica': PURPLE, 'Europa Des.': '#06B6D4',
    'Asia Des.': '#EC4899', 'Asia Eme.': AMBER,
    'Latam Eme. ex-Chile': '#F97316', 'Globales': '#8B5CF6',
    'Europa Eme.': '#14B8A6', 'Global Des.': '#A78BFA',
    'Global Eme.': '#FB923C', 'Africa Eme.': '#84CC16',
    'Temáticos': '#F43F5E', 'Otros': '#94A3B8', 'Balanceado': SLATE,
};
const getColor = (c) => CLASE_COLORS[c] || SLATE;

/* Parsea "CLP 100.00%" → { clase: "CLP", pct: 100.0 } */
function parseDominancia(str) {
    if (!str) return { clase: '-', pct: null };
    const m = String(str).match(/^(.+?)\s+([\d.]+)%*$/);
    if (!m) return { clase: String(str), pct: null };
    return { clase: m[1].trim(), pct: parseFloat(m[2]) };
}

function fmtPct(val) {
    if (val == null || val === '') return '-';
    const n = parseFloat(val);
    if (isNaN(n)) return '-';
    return `${n % 1 === 0 ? n.toFixed(0) : parseFloat(n.toFixed(2))}%`;
}

function ExternalLinkIcon() {
    return (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
            <polyline points="15 3 21 3 21 9" />
            <line x1="10" y1="14" x2="21" y2="3" />
        </svg>
    );
}

/* ══════════════════════════════════════════════
   Keyframe animations (inyectadas una sola vez)
══════════════════════════════════════════════ */
function AnimStyles() {
    return (
        <style>{`
            @keyframes growBar {
                from { transform: scaleY(0); }
                to   { transform: scaleY(1); }
            }
            @keyframes popSlice {
                from { transform: scale(0); }
                to   { transform: scale(1); }
            }
            @keyframes fadeInLegend {
                from { opacity: 0; transform: translateY(6px); }
                to   { opacity: 1; transform: translateY(0); }
            }
        `}</style>
    );
}

/* ══════════════════════════════════════════════
   MetricCard — ultra-compacta (horizontal layout)
══════════════════════════════════════════════ */
function MetricCard({ label, value, sub, accent = TEAL, icon, tooltip }) {
    const [showTip, setShowTip] = useState(false);
    return (
        <div className="card-hover" style={{
            flex: '1 1 0', minWidth: 130,
            backgroundColor: '#FFFFFF',
            borderRadius: 12, border: '1px solid #DDE3E6',
            boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
            padding: '12px 16px',
            display: 'flex', flexDirection: 'column', gap: 4,
        }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <p style={{ fontSize: 9, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#9F9F9F', margin: 0 }}>{label}</p>
                <div
                    style={{ position: 'relative' }}
                    onMouseEnter={() => tooltip && setShowTip(true)}
                    onMouseLeave={() => setShowTip(false)}
                >
                    <div style={{ width: 22, height: 22, borderRadius: 6, backgroundColor: accent + '18', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: tooltip ? 'help' : 'default' }}>
                        {icon}
                    </div>
                    {showTip && tooltip && (
                        <div style={{
                            position: 'absolute', bottom: 'calc(100% + 7px)', right: 0,
                            backgroundColor: '#191919', color: '#FFFFFF',
                            fontSize: 11, fontWeight: 500, lineHeight: 1.45,
                            padding: '7px 10px', borderRadius: 8,
                            zIndex: 60, width: 190,
                            boxShadow: '0 4px 16px rgba(0,0,0,0.18)',
                            animation: 'fadeIn 0.15s ease both',
                            pointerEvents: 'none',
                        }}>
                            {tooltip}
                            <span style={{ position: 'absolute', top: '100%', right: 8, width: 0, height: 0, borderStyle: 'solid', borderWidth: '5px 5px 0', borderColor: '#191919 transparent transparent' }} />
                        </div>
                    )}
                </div>
            </div>
            <p style={{ fontSize: 20, fontWeight: 800, color: '#191919', margin: 0, lineHeight: 1.1 }}>{value}</p>
            {sub && <p style={{ fontSize: 10, color: '#71717A', margin: 0 }}>{sub}</p>}
        </div>
    );
}

/* ══════════════════════════════════════════════
   Bar Chart — Antigua vs Nueva (top 5 clases)
══════════════════════════════════════════════ */
function BarChart({ breakdownAntigua, breakdownNueva, label }) {
    const [tipBar, setTipBar] = useState(null);
    // Unir clases y ordenar por valor descendente (suma de antigua+nueva)
    const allClases = [...new Set([
        ...breakdownAntigua.map(d => d.clase),
        ...breakdownNueva.map(d => d.clase),
    ])];

    if (allClases.length === 0) {
        return <p style={{ color: '#9F9F9F', fontSize: 12, textAlign: 'center', padding: '20px 0' }}>Sin datos de composición</p>;
    }

    // Ordenar por valor descendente (antigua+nueva)
    const barData = allClases.map(c => ({
        clase: c,
        antigua: breakdownAntigua.find(x => x.clase === c)?.pct ?? 0,
        nueva: breakdownNueva.find(x => x.clase === c)?.pct ?? 0,
        color: getColor(c),
    })).sort((a, b) => (b.antigua + b.nueva) - (a.antigua + a.nueva));

    const maxVal = Math.max(...barData.flatMap(d => [Math.abs(d.antigua), Math.abs(d.nueva)]), 1);
    const chartH = 100;
    const barW = 20;
    const gap = 6;
    const groupW = barW * 2 + gap + 20;
    const MIN_SLOTS = 5; // siempre reservar al menos 5 grupos para mantener proporciones
    const slots = Math.max(barData.length, MIN_SLOTS);
    const totalW = slots * groupW;

    // Helper para truncar nombres largos
    function truncateLabel(label, maxLen = 12) {
        return label.length > maxLen ? label.slice(0, maxLen - 2) + '…' : label;
    }

    return (
        <div style={{ width: '100%', overflowX: 'auto' }}>
            <svg width="100%" viewBox={`0 0 ${totalW + 40} ${chartH + 56}`} style={{ display: 'block', minWidth: 280, overflow: 'visible' }}>
                {[0, 0.5, 1].map((t, i) => {
                    const val = Math.round(maxVal * t);
                    const y = chartH - (val / maxVal) * chartH + 20;
                    return (
                        <g key={i}>
                            <line x1="30" y1={y} x2={totalW + 40} y2={y} stroke="#F0F0F0" strokeWidth="1" />
                            <text x="26" y={y + 4} textAnchor="end" fontSize="8" fill="#9F9F9F">{val}%</text>
                        </g>
                    );
                })}
                {barData.map((d, i) => {
                    const x = 36 + i * groupW;
                    const hA = (Math.abs(d.antigua) / maxVal) * chartH;
                    const hN = (Math.abs(d.nueva) / maxVal) * chartH;
                    // Etiqueta truncada y tooltip
                    const labelShort = truncateLabel(d.clase);
                    return (
                        <g key={d.clase}>
                            <rect x={x} y={chartH - hA + 20} width={barW} height={Math.max(hA, 1)} rx="3" fill={TEAL}
                                fillOpacity={tipBar?.idx === i && tipBar?.type === 'a' ? 1 : 0.9}
                                style={{ transformBox: 'fill-box', transformOrigin: 'bottom', animation: 'growBar 0.5s cubic-bezier(0.34,1.4,0.64,1) both', animationDelay: `${i * 0.07}s`, transition: 'fill-opacity 0.15s', cursor: 'crosshair' }}
                                onMouseEnter={() => d.antigua > 0 && setTipBar({ idx: i, type: 'a', val: d.antigua, x: x + barW / 2, y: chartH - hA + 20 })}
                                onMouseLeave={() => setTipBar(null)} />
                            <rect x={x + barW + gap} y={chartH - hN + 20} width={barW} height={Math.max(hN, 1)} rx="3" fill={PURPLE}
                                fillOpacity={tipBar?.idx === i && tipBar?.type === 'n' ? 1 : 0.85}
                                style={{ transformBox: 'fill-box', transformOrigin: 'bottom', animation: 'growBar 0.5s cubic-bezier(0.34,1.4,0.64,1) both', animationDelay: `${i * 0.07 + 0.035}s`, transition: 'fill-opacity 0.15s', cursor: 'crosshair' }}
                                onMouseEnter={() => d.nueva > 0 && setTipBar({ idx: i, type: 'n', val: d.nueva, x: x + barW + gap + barW / 2, y: chartH - hN + 20 })}
                                onMouseLeave={() => setTipBar(null)} />
                            <text x={x + barW / 2} y={Math.min(chartH - hA + 15, chartH + 15)} textAnchor="middle" fontSize="7" fill={TEAL} fontWeight="700"
                                style={{ animation: 'fadeInLegend 0.35s ease both', animationDelay: `${i * 0.07 + 0.3}s` }}>{d.antigua > 0 ? `${d.antigua}%` : ''}</text>
                            <text x={x + barW + gap + barW / 2} y={Math.min(chartH - hN + 15, chartH + 15)} textAnchor="middle" fontSize="7" fill={PURPLE} fontWeight="700"
                                style={{ animation: 'fadeInLegend 0.35s ease both', animationDelay: `${i * 0.07 + 0.335}s` }}>{d.nueva > 0 ? `${d.nueva}%` : ''}</text>
                            {/* Etiqueta rotada, truncada y con tooltip */}
                            <g>
                                <title>{d.clase}</title>
                                <text
                                    x={x + barW + gap / 2}
                                    y={chartH + 44}
                                    textAnchor="end"
                                    fontSize="9"
                                    fontWeight="600"
                                    fill="#525256"
                                    transform={`rotate(-35 ${x + barW + gap / 2},${chartH + 44})`}
                                    style={{ cursor: d.clase.length > 12 ? 'help' : 'default', animation: 'fadeInLegend 0.35s ease both', animationDelay: `${i * 0.07 + 0.25}s` }}
                                >
                                    {labelShort}
                                </text>
                            </g>
                        </g>
                    );
                })}
                {tipBar && (
                    <g style={{ pointerEvents: 'none' }}>
                        <rect x={tipBar.x - 25} y={tipBar.y - 23} width={50} height={18} rx={4} fill="#191919" fillOpacity={0.88} />
                        <text x={tipBar.x} y={tipBar.y - 9} textAnchor="middle" fontSize="9" fill="#FFFFFF" fontWeight="700">{tipBar.val.toFixed(1)}%</text>
                    </g>
                )}
            </svg>
            <div style={{ display: 'flex', gap: 16, justifyContent: 'center', marginTop: 2 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                    <span style={{ width: 10, height: 10, borderRadius: 2, backgroundColor: TEAL, display: 'inline-block' }} />
                    <span style={{ fontSize: 11, color: '#71717A' }}>{label} Antigua</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                    <span style={{ width: 10, height: 10, borderRadius: 2, backgroundColor: PURPLE, display: 'inline-block' }} />
                    <span style={{ fontSize: 11, color: '#71717A' }}>{label} Nueva</span>
                </div>
            </div>
        </div>
    );
}

/* ══════════════════════════════════════════════
   Pie (donut) — composición nueva
══════════════════════════════════════════════ */
function PieChart({ breakdownNueva }) {
    const [hovered, setHovered] = useState(null);
    const slicesRaw = (breakdownNueva || []).filter(d => d.pct > 0);

    if (slicesRaw.length === 0) {
        return <p style={{ color: '#9F9F9F', fontSize: 12, textAlign: 'center', padding: '20px 0' }}>Sin datos</p>;
    }

    const total = slicesRaw.reduce((s, d) => s + d.pct, 0);
    const slices = slicesRaw.reduce((acc, d, i) => {
        const start = i === 0 ? 0 : acc[i - 1].end;
        acc.push({ ...d, start, end: start + (d.pct / total) * 360, color: getColor(d.clase) });
        return acc;
    }, []);

    function polarXY(angle, r) {
        const rad = ((angle - 90) * Math.PI) / 180;
        return { x: 64 + r * Math.cos(rad), y: 64 + r * Math.sin(rad) };
    }
    function slicePath(s, e, inner = 34, outer = 58) {
        const a = polarXY(s, outer), b = polarXY(e, outer);
        const c = polarXY(e, inner), dd = polarXY(s, inner);
        const lg = (e - s) > 180 ? 1 : 0;
        return `M ${a.x} ${a.y} A ${outer} ${outer} 0 ${lg} 1 ${b.x} ${b.y} L ${c.x} ${c.y} A ${inner} ${inner} 0 ${lg} 0 ${dd.x} ${dd.y} Z`;
    }

    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <svg viewBox="0 0 128 128" style={{ width: 148, height: 148, flexShrink: 0 }}>
                {slices.map((s, i) => (
                    <path key={i} d={slicePath(s.start, s.end)}
                        fill={s.color} fillOpacity={hovered === i ? 1 : 0.82}
                        stroke="#FFFFFF" strokeWidth="1.5"
                        style={{
                            cursor: 'pointer',
                            transition: 'fill-opacity 0.2s',
                            transformBox: 'fill-box',
                            transformOrigin: 'center',
                            animation: 'popSlice 0.45s cubic-bezier(0.34,1.5,0.64,1) both',
                            animationDelay: `${i * 0.08}s`,
                        }}
                        onMouseEnter={() => setHovered(i)} onMouseLeave={() => setHovered(null)} />
                ))}
                <text x="64" y="60" textAnchor="middle" fontSize="11" fontWeight="800" fill="#191919">{slices[0]?.clase}</text>
                <text x="64" y="74" textAnchor="middle" fontSize="9" fill="#9F9F9F">dominante</text>
            </svg>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
                {slices.map((s, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ width: 10, height: 10, borderRadius: 3, backgroundColor: s.color, flexShrink: 0 }} />
                        <div>
                            <p style={{ margin: 0, fontSize: 13, fontWeight: 700, color: '#191919' }}>{s.clase}</p>
                            <p style={{ margin: 0, fontSize: 12, color: '#71717A', lineHeight: 1.3 }}>{fmtPct(s.pct)}</p>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

/* ══════════════════════════════════════════════
   SectionCard compacta
══════════════════════════════════════════════ */
function SectionCard({ title, children }) {
    return (
        <div className="card-hover" style={{ backgroundColor: '#FFFFFF', borderRadius: 14, border: '1px solid #DDE3E6', boxShadow: '0 2px 4px rgba(0,0,0,0.04)', overflow: 'hidden' }}>
            <div style={{ padding: '12px 18px', borderBottom: '1px solid #F0F0F0' }}>
                <h2 style={{ margin: 0, fontSize: 12, fontWeight: 700, color: '#191919' }}>{title}</h2>
            </div>
            <div style={{ padding: '14px 18px' }}>{children}</div>
        </div>
    );
}

/* ══════════════════════════════════════════════
   PÁGINA PRINCIPAL
══════════════════════════════════════════════ */
export default function VisualizacionPage({ selectedId: propId, onSelect }) {
    const { validationData, activeClasificacion } = useApp();
    const toast = useToast();
    const [selectedId, setSelectedId] = useState(propId ?? null);
    const [searchId, setSearchId] = useState('');
    const [detail, setDetail] = useState(null);
    const [loadingDetail, setLoadingDetail] = useState(false);
    // Revisiones state (localStorage, compartido con ValidacionPage, separado por clasificación)
    const [revisiones, setRevisiones] = useState(() => {
        try {
            const key = activeClasificacion ? `allocations_revisiones_${activeClasificacion}` : 'allocations_revisiones';
            const saved = localStorage.getItem(key);
            return saved ? JSON.parse(saved) : {};
        } catch { return {}; }
    });
    // Persist revisiones to localStorage
    useEffect(() => {
        const key = activeClasificacion ? `allocations_revisiones_${activeClasificacion}` : 'allocations_revisiones';
        try {
            localStorage.setItem(key, JSON.stringify(revisiones));
        } catch {}
    }, [revisiones, activeClasificacion]);


    // Sincronizar con selección externa (desde la tabla)
    useEffect(() => {
        if (propId != null && propId !== selectedId) {
            setSelectedId(propId);
            setSearchId('');
        }
    }, [propId]);

    // Obtener breakdown al cambiar instrumento o clasificación activa
    useEffect(() => {
        if (selectedId == null) return;
        setDetail(null);
        setLoadingDetail(true);
        getInstrumentDetail(selectedId, activeClasificacion || null)
            .then(data => setDetail(data))
            .catch(() => setDetail(null))
            .finally(() => setLoadingDetail(false));
    }, [selectedId, activeClasificacion]);

    const handleSearch = (val) => {
        setSearchId(val);
        const id = parseInt(val);
        if (!isNaN(id) && validationData?.find(r => Number(r.ID) === id)) {
            setSelectedId(id);
            onSelect?.(id);
        }
    };

    // Sin datos procesados aún
    if (!validationData || validationData.length === 0) {
        return (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 300, color: '#71717A', fontSize: 14 }}>
                No hay datos procesados. Ejecuta el pipeline desde la página de Inicio.
            </div>
        );
    }


    // Buscar fila del instrumento seleccionado
    const row = validationData.find(r => Number(r.ID) === Number(selectedId));
    if (!row) {
        return (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 300, color: '#71717A', fontSize: 14 }}>
                Selecciona un instrumento desde la tabla de Validación para ver su detalle.
            </div>
        );
    }
    const revision = revisiones[row.ID] || 'Sin revisar';

    // Compact validate/reject handlers (now have access to row)
    const handleValidar = () => {
        setRevisiones(prev => {
            const next = { ...prev, [row.ID]: 'Validado' };
            return next;
        });
        if (toast) toast({ message: 'Instrumento validado correctamente', type: 'success' });
    };
    const handleRechazar = () => {
        setRevisiones(prev => {
            const next = { ...prev, [row.ID]: 'Rechazado' };
            return next;
        });
        if (toast) toast({ message: 'Instrumento rechazado', type: 'warning' });
    };

    // Detectar pipeline (moneda vs región vs industria)
    const isMoneda = 'moneda_antigua' in row;
    const isRegion = 'region_antigua' in row;
    const labelClase = isMoneda ? 'Moneda' : isRegion ? 'Región' : 'Industria';
    const labelDivisas = isMoneda ? 'divisas' : isRegion ? 'regiones' : 'industrias';

    // Parsear campos de dominancia
    const domAntigua = parseDominancia(row.pct_dominancia_antigua);
    const domNuevaRaw = row.pct_dominancia_nuevo ?? row.pct_dominancia_nueva;
    const domNueva = parseDominancia(domNuevaRaw);

    // Clase antigua y nueva (para el resumen bajo el pie)
    const claseAntigua = row.moneda_antigua ?? row.region_antigua ?? row.sector_antigua ?? '-';
    const claseNueva = row.moneda_nueva ?? row.region_nueva ?? row.sector_nueva ?? '-';

    // Datos de los gráficos
    const breakdownAntigua = detail?.breakdown_antigua ?? [];
    const breakdownNueva = detail?.breakdown_nueva ?? [];
    const countNueva = detail?.count_nueva ?? breakdownNueva.length;
    const hasDatos = row.Cambio !== 'Sin datos';

    /* Icono SVG helper */
    const I = (stroke, d) => (
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            {d}
        </svg>
    );

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, padding: '22px 28px', width: '100%', maxWidth: 1400, margin: '0 auto' }}>
            <AnimStyles />

            {/* ── Cabecera ── */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 3 }}>
                        <h1 style={{ fontSize: 16, fontWeight: 700, color: '#191919', margin: 0, lineHeight: 1.2 }}>
                            {row.Nombre}
                        </h1>
                        <button
                            onClick={() => window.open(`https://web.finantech.cl/admin/instruments/${row.ID}`, '_blank')}
                            title="Ver en Finantech"
                            style={{
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                width: 24, height: 24, borderRadius: 6, border: 'none',
                                backgroundColor: 'transparent', color: '#9F9F9F', cursor: 'pointer',
                                transition: 'all 0.15s', flexShrink: 0
                            }}
                            onMouseEnter={e => { e.currentTarget.style.backgroundColor = '#EBF7F6'; e.currentTarget.style.color = '#299D91'; }}
                            onMouseLeave={e => { e.currentTarget.style.backgroundColor = 'transparent'; e.currentTarget.style.color = '#9F9F9F'; }}
                        >
                            <ExternalLinkIcon />
                        </button>
                        {/* Validar/Rechazar compact buttons */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginLeft: 10 }}>
                            <button
                                onClick={handleValidar}
                                disabled={revision === 'Validado'}
                                style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '5px 10px', borderRadius: 7, fontSize: 12, fontWeight: 700, cursor: revision === 'Validado' ? 'default' : 'pointer', border: 'none', backgroundColor: '#299D91', color: '#FFFFFF', opacity: revision === 'Validado' ? 0.45 : 1, minWidth: 0 }}
                                title="Validar instrumento"
                            >
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 1 }}>
                                    <polyline points="20 6 9 17 4 12" />
                                </svg>
                                Validar
                            </button>
                            <button
                                onClick={handleRechazar}
                                disabled={revision === 'Rechazado'}
                                style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '5px 10px', borderRadius: 7, fontSize: 12, fontWeight: 700, cursor: revision === 'Rechazado' ? 'default' : 'pointer', border: 'none', backgroundColor: '#D94A38', color: '#FFFFFF', opacity: revision === 'Rechazado' ? 0.45 : 1, minWidth: 0 }}
                                title="Rechazar instrumento"
                            >
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 1 }}>
                                    <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                                </svg>
                                Rechazar
                            </button>
                        </div>
                    </div>
                </div>

                {/* Buscador por ID */}
                <div style={{
                    display: 'flex', alignItems: 'center', gap: 8,
                    padding: '6px 14px', borderRadius: 10,
                    border: '1px solid #DDE3E6', backgroundColor: '#FFFFFF',
                    boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
                    width: 140, transition: 'border-color 0.2s'
                }}
                    onFocusCapture={e => e.currentTarget.style.borderColor = TEAL}
                    onBlurCapture={e => e.currentTarget.style.borderColor = '#DDE3E6'}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#9F9F9F" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
                    </svg>
                    <input
                        type="text"
                        placeholder="Buscar ID..."
                        value={searchId}
                        onChange={e => handleSearch(e.target.value)}
                        style={{
                            border: 'none', outline: 'none', background: 'transparent',
                            fontSize: 12, fontWeight: 700, color: '#191919', width: '100%'
                        }}
                    />
                </div>
            </div>

            {/* ══ MÉTRICAS — 4 tarjetas ══ */}
            <div className="anim-fade-slide-delay-1" style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                <MetricCard
                    label="PCT Original"
                    value={fmtPct(row.pct_original)}
                    sub="% cubierto antes del escalado"
                    accent={TEAL}
                    tooltip="Porcentaje de la posición total cubierto por las allocations originales, antes del escalado al 100%."
                    icon={I(TEAL, <><line x1="19" y1="5" x2="5" y2="19" /><circle cx="6.5" cy="6.5" r="2.5" /><circle cx="17.5" cy="17.5" r="2.5" /></>)}
                />
                <MetricCard
                    label={`PCT Dom. Antigua`}
                    value={fmtPct(domAntigua.pct)}
                    sub={domAntigua.clase !== '-' ? `${labelClase}: ${domAntigua.clase}` : 'Sin datos'}
                    accent={PURPLE}
                    tooltip={`Porcentaje de dominancia de la ${labelClase} en la allocación antigua.`}
                    icon={I(PURPLE, <><polyline points="22 7 13.5 15.5 8.5 10.5 2 17" /><polyline points="16 7 22 7 22 13" /></>)}
                />
                <MetricCard
                    label={`PCT Dom. Nueva`}
                    value={hasDatos ? fmtPct(domNueva.pct) : '-'}
                    sub={hasDatos && domNueva.clase !== '-' ? `${labelClase}: ${domNueva.clase}` : 'Sin datos'}
                    accent={hasDatos ? TEAL : SLATE}
                    tooltip={`Porcentaje de dominancia de la ${labelClase} en la allocación nueva.`}
                    icon={I(hasDatos ? TEAL : SLATE, <><polyline points="23 6 13.5 15.5 8.5 10.5 1 18" /><polyline points="17 6 23 6 23 12" /></>)}
                />
                <MetricCard
                    label="Tipo Instrumento"
                    value={row['Tipo instrumento'] ?? '-'}
                    sub="Clasificación regulatoria"
                    accent={AMBER}
                    tooltip="Clasificación regulatoria del instrumento según el maestro de instrumentos."
                    icon={I(AMBER, <><rect x="2" y="3" width="20" height="14" rx="2" /><path d="M8 21h8M12 17v4" /></>)}
                />
            </div>

            {/* ══ GRÁFICOS ══ */}
            <div className="anim-fade-slide-delay-2" style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 14 }}>
                <SectionCard title={`% por ${labelClase} — Antigua vs Nueva`}>
                    {loadingDetail ? (
                        <div style={{ padding: '4px 0 10px' }}>
                            <div className="skeleton" style={{ height: 120, width: '100%', borderRadius: 8 }} />
                            <div style={{ display: 'flex', gap: 16, justifyContent: 'center', marginTop: 12 }}>
                                <div className="skeleton" style={{ height: 12, width: 90 }} />
                                <div className="skeleton" style={{ height: 12, width: 90 }} />
                            </div>
                        </div>
                    ) : !hasDatos ? (
                        <p style={{ color: '#9F9F9F', fontSize: 12, textAlign: 'center', padding: '24px 0' }}>Sin datos de composición para este instrumento</p>
                    ) : (
                        <BarChart key={selectedId} breakdownAntigua={breakdownAntigua} breakdownNueva={breakdownNueva} label={labelClase} />
                    )}
                </SectionCard>

                <SectionCard title={`Composición ${labelClase} Nueva`}>
                    {loadingDetail ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                            <div className="skeleton" style={{ width: 148, height: 148, borderRadius: '50%', flexShrink: 0 }} />
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, flex: 1 }}>
                                {[...Array(4)].map((_, i) => (
                                    <div key={i} className="skeleton" style={{ height: 13, width: `${70 - i * 10}%` }} />
                                ))}
                            </div>
                        </div>
                    ) : !hasDatos ? (
                        <p style={{ color: '#9F9F9F', fontSize: 12, textAlign: 'center', padding: '24px 0' }}>Sin datos</p>
                    ) : (
                        <>
                            <PieChart key={selectedId} breakdownNueva={breakdownNueva} />
                            <div style={{ marginTop: 14, paddingTop: 12, borderTop: '1px solid #F5F5F5' }}>
                                {[
                                    { label: `${labelClase} antigua`, value: claseAntigua },
                                    { label: `${labelClase} nueva dom.`, value: domNueva.clase },
                                    { label: `Nº ${labelDivisas} nuevas`, value: countNueva || '-' },
                                ].map((item, i) => (
                                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                                        <span style={{ fontSize: 11, color: '#71717A' }}>{item.label}</span>
                                        <span style={{ fontSize: 11, fontWeight: 700, color: '#191919' }}>{item.value ?? '-'}</span>
                                    </div>
                                ))}
                            </div>
                        </>
                    )}
                </SectionCard>
            </div>

        </div>
    );
}

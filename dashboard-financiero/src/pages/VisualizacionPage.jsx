import { useState } from 'react';

/* ══════════════════════════════════════════════
   CATÁLOGO DE INSTRUMENTOS
   (derivado del df_final.csv, con datos de país añadidos)
══════════════════════════════════════════════ */
const INSTRUMENTOS = [
    {
        id: 23,
        nombre: 'FM BCI Gestión Global Dinámica 80',
        tipo: 'C03', pais: 'Chile', cambio: 'Sí',
        pct_original: 77.33, pct_escalado: 100.0,
        pct_dominancia_antigua: 100.0,
        moneda_dominante_antigua: 'CLP',
        monedas_antiguas: [{ moneda: 'CLP', pct: 100.0 }],
        monedas_nuevas: [{ moneda: 'USD', pct: 49.42 }, { moneda: 'EUR', pct: 28.1 }, { moneda: 'JPY', pct: 12.8 }, { moneda: 'Otros', pct: 9.68 }],
    },
    {
        id: 31,
        nombre: 'MFS European Value Fund - A1',
        tipo: 'C03', pais: 'Luxembourg', cambio: 'No',
        pct_original: 99.9, pct_escalado: 100.0,
        pct_dominancia_antigua: 52.02,
        moneda_dominante_antigua: 'EUR',
        monedas_antiguas: [{ moneda: 'EUR', pct: 52.02 }, { moneda: 'GBP', pct: 30.0 }, { moneda: 'Otros', pct: 17.98 }],
        monedas_nuevas: [{ moneda: 'EUR', pct: 52.02 }, { moneda: 'GBP', pct: 25.1 }, { moneda: 'USD', pct: 14.5 }, { moneda: 'Otros', pct: 8.38 }],
    },
    {
        id: 149,
        nombre: 'iShares MSCI ACWI ETF (ACWI)',
        tipo: 'C09', pais: 'Estados Unidos', cambio: 'No',
        pct_original: 94.23, pct_escalado: 100.0,
        pct_dominancia_antigua: 69.81,
        moneda_dominante_antigua: 'USD',
        monedas_antiguas: [{ moneda: 'USD', pct: 69.81 }, { moneda: 'EUR', pct: 15.0 }, { moneda: 'Otros', pct: 15.19 }],
        monedas_nuevas: [{ moneda: 'USD', pct: 69.81 }, { moneda: 'EUR', pct: 12.5 }, { moneda: 'JPY', pct: 6.4 }, { moneda: 'GBP', pct: 5.0 }, { moneda: 'Otros', pct: 6.29 }],
    },
    {
        id: 692,
        nombre: 'PIMCO GIS Total Return Bond Fund E',
        tipo: 'C03', pais: 'Irlanda', cambio: 'Sí',
        pct_original: 0.8, pct_escalado: 100.0,
        pct_dominancia_antigua: 100.0,
        moneda_dominante_antigua: 'USD',
        monedas_antiguas: [{ moneda: 'USD', pct: 100.0 }],
        monedas_nuevas: [{ moneda: 'BRL', pct: 131.25 }],
    },
    {
        id: 389,
        nombre: 'Vanguard FTSE Emerging Markets ETF',
        tipo: 'C09', pais: 'Estados Unidos', cambio: 'No',
        pct_original: 86.68, pct_escalado: 100.0,
        pct_dominancia_antigua: 27.23,
        moneda_dominante_antigua: 'HKD',
        monedas_antiguas: [{ moneda: 'HKD', pct: 27.23 }, { moneda: 'CNY', pct: 22.5 }, { moneda: 'TWD', pct: 18.0 }, { moneda: 'Otros', pct: 32.27 }],
        monedas_nuevas: [{ moneda: 'HKD', pct: 27.23 }, { moneda: 'CNY', pct: 22.1 }, { moneda: 'TWD', pct: 16.4 }, { moneda: 'INR', pct: 14.5 }, { moneda: 'Otros', pct: 19.77 }],
    },
];

/* ── Paleta ── */
const TEAL = '#299D91';
const PURPLE = '#6366F1';
const AMBER = '#F0A050';
const RED = '#E05252';
const SLATE = '#64748B';

const CCY_COLORS = {
    'USD': TEAL, 'EUR': PURPLE, 'CLP': AMBER, 'JPY': '#06B6D4',
    'GBP': '#8B5CF6', 'HKD': '#EC4899', 'BRL': '#F97316',
    'CNY': '#14B8A6', 'TWD': '#A78BFA', 'INR': '#FB923C',
    'Balanceado': SLATE, 'Otros': '#94A3B8',
};
const getCCYColor = (m) => CCY_COLORS[m] || SLATE;

/* ══════════════════════════════════════════════
   MetricCard — ultra-compacta (horizontal layout)
══════════════════════════════════════════════ */
function MetricCard({ label, value, sub, accent = TEAL, icon }) {
    return (
        <div style={{
            flex: '1 1 0', minWidth: 130,
            backgroundColor: '#FFFFFF',
            borderRadius: 12, border: '1px solid #DDE3E6',
            boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
            padding: '12px 16px',
            display: 'flex', flexDirection: 'column', gap: 4,
        }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <p style={{ fontSize: 9, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#9F9F9F', margin: 0 }}>{label}</p>
                <div style={{ width: 22, height: 22, borderRadius: 6, backgroundColor: accent + '18', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {icon}
                </div>
            </div>
            <p style={{ fontSize: 20, fontWeight: 800, color: '#191919', margin: 0, lineHeight: 1.1 }}>{value}</p>
            {sub && <p style={{ fontSize: 10, color: '#71717A', margin: 0 }}>{sub}</p>}
        </div>
    );
}

/* ══════════════════════════════════════════════
   Bar Chart — Moneda Antigua vs Nueva (% por divisa)
   Altura reducida para caber en una vista
══════════════════════════════════════════════ */
function BarChart({ instrumento }) {
    const allMonedas = [...new Set([
        ...instrumento.monedas_antiguas.map(m => m.moneda),
        ...instrumento.monedas_nuevas.map(m => m.moneda),
    ])];
    const barData = allMonedas.map(m => ({
        moneda: m,
        antigua: instrumento.monedas_antiguas.find(x => x.moneda === m)?.pct ?? 0,
        nueva: instrumento.monedas_nuevas.find(x => x.moneda === m)?.pct ?? 0,
        color: getCCYColor(m),
    }));

    const maxVal = Math.max(...barData.flatMap(d => [Math.abs(d.antigua), Math.abs(d.nueva)]), 1);
    const chartH = 100; /* ← reducida para caber en una vista */
    const barW = 20;
    const gap = 6;
    const groupW = barW * 2 + gap + 20;
    const totalW = barData.length * groupW;

    return (
        <div style={{ width: '100%', overflowX: 'auto' }}>
            <svg width="100%" viewBox={`0 0 ${totalW + 40} ${chartH + 56}`} style={{ display: 'block', minWidth: 280 }}>
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
                    return (
                        <g key={d.moneda}>
                            <rect x={x} y={chartH - hA + 20} width={barW} height={Math.max(hA, 1)} rx="3" fill={TEAL} fillOpacity="0.9" />
                            <rect x={x + barW + gap} y={chartH - hN + 20} width={barW} height={Math.max(hN, 1)} rx="3" fill={PURPLE} fillOpacity="0.85" />
                            {/* Porcentaje SIEMPRE encima de la barra, incluso si es pequeña */}
                            <text x={x + barW / 2} y={Math.min(chartH - hA + 15, chartH + 15)} textAnchor="middle" fontSize="7" fill={TEAL} fontWeight="700">{d.antigua > 0 ? `${d.antigua}%` : ''}</text>
                            <text x={x + barW + gap + barW / 2} y={Math.min(chartH - hN + 15, chartH + 15)} textAnchor="middle" fontSize="7" fill={PURPLE} fontWeight="700">{d.nueva > 0 ? `${d.nueva}%` : ''}</text>
                            <text x={x + barW + gap / 2} y={chartH + 34} textAnchor="middle" fontSize="10" fontWeight="600" fill="#525256">{d.moneda}</text>
                        </g>
                    );
                })}
            </svg>
            <div style={{ display: 'flex', gap: 16, justifyContent: 'center', marginTop: 2 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                    <span style={{ width: 10, height: 10, borderRadius: 2, backgroundColor: TEAL, display: 'inline-block' }} />
                    <span style={{ fontSize: 11, color: '#71717A' }}>Moneda Antigua</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                    <span style={{ width: 10, height: 10, borderRadius: 2, backgroundColor: PURPLE, display: 'inline-block' }} />
                    <span style={{ fontSize: 11, color: '#71717A' }}>Moneda Nueva</span>
                </div>
            </div>
        </div>
    );
}

/* ══════════════════════════════════════════════
   Pie (donut) — reducida
══════════════════════════════════════════════ */
function PieChart({ instrumento }) {
    const [hovered, setHovered] = useState(null);
    const slicesRaw = instrumento.monedas_nuevas.filter(m => m.pct > 0);
    const total = slicesRaw.reduce((s, d) => s + d.pct, 0);
    const slices = slicesRaw.reduce((acc, d, i) => {
        const start = i === 0 ? 0 : acc[i - 1].end;
        acc.push({ ...d, start, end: start + (d.pct / total) * 360, color: getCCYColor(d.moneda) });
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
                        style={{ cursor: 'pointer', transition: 'fill-opacity 0.2s' }}
                        onMouseEnter={() => setHovered(i)} onMouseLeave={() => setHovered(null)} />
                ))}
                <text x="64" y="60" textAnchor="middle" fontSize="11" fontWeight="800" fill="#191919">{instrumento.monedas_nuevas[0]?.moneda}</text>
                <text x="64" y="74" textAnchor="middle" fontSize="9" fill="#9F9F9F">dominante</text>
            </svg>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
                {slices.map((s, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ width: 10, height: 10, borderRadius: 3, backgroundColor: s.color, flexShrink: 0 }} />
                        <div>
                            <p style={{ margin: 0, fontSize: 13, fontWeight: 700, color: '#191919' }}>{s.moneda}</p>
                            <p style={{ margin: 0, fontSize: 12, color: '#71717A', lineHeight: 1.3 }}>{s.pct.toFixed(1)}%</p>
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
        <div style={{ backgroundColor: '#FFFFFF', borderRadius: 14, border: '1px solid #DDE3E6', boxShadow: '0 2px 4px rgba(0,0,0,0.04)', overflow: 'hidden' }}>
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
export default function VisualizacionPage() {
    const [selectedId, setSelectedId] = useState(INSTRUMENTOS[0].id);
    const inst = INSTRUMENTOS.find(i => i.id === selectedId);

    const delta = (inst.pct_escalado - inst.pct_original).toFixed(2);
    const isUp = parseFloat(delta) >= 0;
    const hasCambio = inst.cambio === 'Sí';

    /* ── Iconos SVG (tamaño 13) ── */
    const I = (stroke, d) => (
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            {d}
        </svg>
    );

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, padding: '22px 28px', width: '100%', maxWidth: 1400, margin: '0 auto' }}>

            {/* ── Cabecera ultracompacta ── */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
                <div>
                    <p style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase', color: '#9F9F9F', margin: 0 }}>
                        VISUALIZACIÓN · Instrumento
                    </p>
                    <h1 style={{ fontSize: 16, fontWeight: 700, color: '#191919', margin: '3px 0 0', lineHeight: 1.2 }}>
                        {inst.nombre}
                    </h1>
                </div>
                <select value={selectedId} onChange={e => setSelectedId(Number(e.target.value))}
                    style={{ padding: '7px 14px', borderRadius: 10, border: '1px solid #DDE3E6', backgroundColor: '#FFFFFF', fontSize: 12, fontWeight: 600, color: '#191919', cursor: 'pointer', outline: 'none', maxWidth: 320, boxShadow: '0 1px 2px rgba(0,0,0,0.04)' }}>
                    {INSTRUMENTOS.map(i => <option key={i.id} value={i.id}>{i.nombre}</option>)}
                </select>
            </div>

            {/* ══ MÉTRICAS — 5 tarjetas compactas ══ */}
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                <MetricCard
                    label="PCT Original"
                    value={`${inst.pct_original}%`}
                    sub="Previo al escalado"
                    accent={TEAL}
                    icon={I(TEAL, <><line x1="19" y1="5" x2="5" y2="19" /><circle cx="6.5" cy="6.5" r="2.5" /><circle cx="17.5" cy="17.5" r="2.5" /></>)}
                />
                <MetricCard
                    label="Delta"
                    value={`${isUp ? '+' : ''}${delta}%`}
                    sub="Escalado vs Original"
                    accent={isUp ? TEAL : RED}
                    icon={I(isUp ? TEAL : RED, <><line x1="12" y1="20" x2="12" y2="4" /><polyline points="6 10 12 4 18 10" /></>)}
                />
                <MetricCard
                    label="PCT Dom. Antigua"
                    value={`${inst.pct_dominancia_antigua}%`}
                    sub={`Dominante: ${inst.moneda_dominante_antigua}`}
                    accent={PURPLE}
                    icon={I(PURPLE, <><polyline points="22 7 13.5 15.5 8.5 10.5 2 17" /><polyline points="16 7 22 7 22 13" /></>)}
                />
                <MetricCard
                    label="Tipo Instrumento"
                    value={inst.tipo}
                    sub="Clasificación regulatoria"
                    accent={SLATE}
                    icon={I(SLATE, <><rect x="2" y="3" width="20" height="14" rx="2" /><path d="M8 21h8M12 17v4" /></>)}
                />
                <MetricCard
                    label="País"
                    value={inst.pais}
                    sub="Domicilio del instrumento"
                    accent={AMBER}
                    icon={I(AMBER, <><circle cx="12" cy="12" r="10" /><line x1="2" y1="12" x2="22" y2="12" /><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" /></>)}
                />
            </div>

            {/* ══ GRÁFICOS — barras + torta ══ */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 14 }}>
                <SectionCard title="% por Moneda — Antigua vs Nueva">
                    <BarChart instrumento={inst} />
                </SectionCard>

                <SectionCard title="Composición Moneda Nueva">
                    <PieChart instrumento={inst} />
                    <div style={{ marginTop: 14, paddingTop: 12, borderTop: '1px solid #F5F5F5' }}>
                        {[
                            { label: 'Moneda antigua', value: inst.monedas_antiguas[0]?.moneda },
                            { label: 'Moneda nueva dom.', value: inst.monedas_nuevas[0]?.moneda },
                            { label: 'Nº divisas nuevas', value: inst.monedas_nuevas.length },
                        ].map((item, i) => (
                            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                                <span style={{ fontSize: 11, color: '#71717A' }}>{item.label}</span>
                                <span style={{ fontSize: 11, fontWeight: 700, color: '#191919' }}>{item.value}</span>
                            </div>
                        ))}
                    </div>
                </SectionCard>
            </div>

        </div>
    );
}

import { useState, useMemo } from 'react';

const SAMPLE_DATA = [
    { id: 1, instrumento: 'Bono Gobierno 2025', tipo: 'Renta Fija', estado: 'Válido', region: 'Latam', divisa: 'USD', valor: 125000 },
    { id: 2, instrumento: 'Acción Apple Inc.', tipo: 'Renta Variable', estado: 'Pendiente', region: 'EEUU', divisa: 'USD', valor: 87500 },
    { id: 3, instrumento: 'ETF S&P500', tipo: 'ETF', estado: 'Error', region: 'Global', divisa: 'USD', valor: 340000 },
    { id: 4, instrumento: 'Bono Corporativo BBB', tipo: 'Renta Fija', estado: 'Válido', region: 'Europa', divisa: 'EUR', valor: 95000 },
    { id: 5, instrumento: 'Acción Tesla Inc.', tipo: 'Renta Variable', estado: 'Válido', region: 'EEUU', divisa: 'USD', valor: 210000 },
    { id: 6, instrumento: 'FCI Liquidez', tipo: 'FCI', estado: 'Pendiente', region: 'Local', divisa: 'ARS', valor: 500000 },
    { id: 7, instrumento: 'ON YPF 2027', tipo: 'Renta Fija', estado: 'Error', region: 'Local', divisa: 'USD', valor: 175000 },
    { id: 8, instrumento: 'Acción Amazon.com', tipo: 'Renta Variable', estado: 'Válido', region: 'EEUU', divisa: 'USD', valor: 430000 },
    { id: 9, instrumento: 'Bono EM Asia', tipo: 'Renta Fija', estado: 'Válido', region: 'Asia', divisa: 'USD', valor: 60000 },
    { id: 10, instrumento: 'FCI Acciones', tipo: 'FCI', estado: 'Pendiente', region: 'Local', divisa: 'ARS', valor: 285000 },
    { id: 11, instrumento: 'Acción Microsoft', tipo: 'Renta Variable', estado: 'Válido', region: 'EEUU', divisa: 'USD', valor: 520000 },
    { id: 12, instrumento: 'ETF Nasdaq 100', tipo: 'ETF', estado: 'Válido', region: 'Global', divisa: 'USD', valor: 760000 },
];

const TABS = ['Todos', 'Válido', 'Pendiente', 'Error'];

const ESTADO_CFG = {
    'Válido': { dot: '#299D91', bg: '#EBF7F6', text: '#299D91' },
    'Pendiente': { dot: '#F0A050', bg: '#FFF7ED', text: '#D97706' },
    'Error': { dot: '#E05252', bg: '#FEF2F2', text: '#DC2626' },
};
const TIPO_CFG = {
    'Renta Fija': { bg: '#EEF2FF', text: '#6366F1' },
    'Renta Variable': { bg: '#EBF7F6', text: '#299D91' },
    'ETF': { bg: '#F5F3FF', text: '#7C3AED' },
    'FCI': { bg: '#FFF7ED', text: '#D97706' },
};

function EstadoPill({ estado }) {
    const c = ESTADO_CFG[estado] || {};
    return (
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '4px 10px', borderRadius: '999px', backgroundColor: c.bg, color: c.text, fontSize: '12px', fontWeight: 600, whiteSpace: 'nowrap' }}>
            <span style={{ width: 7, height: 7, borderRadius: '50%', backgroundColor: c.dot, flexShrink: 0 }} />
            {estado}
        </div>
    );
}
function TipoPill({ tipo }) {
    const c = TIPO_CFG[tipo] || { bg: '#F3F4F6', text: '#6B7280' };
    return (
        <span style={{ display: 'inline-flex', alignItems: 'center', padding: '3px 10px', borderRadius: '6px', backgroundColor: c.bg, color: c.text, fontSize: '12px', fontWeight: 500, whiteSpace: 'nowrap' }}>
            {tipo}
        </span>
    );
}
function DotsIcon() {
    return (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="none">
            <circle cx="12" cy="5" r="1.5" /><circle cx="12" cy="12" r="1.5" /><circle cx="12" cy="19" r="1.5" />
        </svg>
    );
}

/* ── Estilos de separador ── */
const borderBottom = { borderBottom: '1px solid #F0F0F0' };
const borderTop = { borderTop: '1px solid #F0F0F0' };

export default function ValidacionPage() {
    const [activeTab, setActiveTab] = useState('Todos');
    const [search, setSearch] = useState('');
    const [selected, setSelected] = useState([]);
    const [page, setPage] = useState(1);
    const rowsPerPage = 10;

    const filtered = useMemo(() =>
        SAMPLE_DATA.filter(r => {
            const matchTab = activeTab === 'Todos' || r.estado === activeTab;
            const matchSearch = !search ||
                r.instrumento.toLowerCase().includes(search.toLowerCase()) ||
                r.tipo.toLowerCase().includes(search.toLowerCase()) ||
                r.region.toLowerCase().includes(search.toLowerCase());
            return matchTab && matchSearch;
        }), [activeTab, search]);

    const totalPages = Math.ceil(filtered.length / rowsPerPage);
    const paged = filtered.slice((page - 1) * rowsPerPage, page * rowsPerPage);
    const totalGeneral = SAMPLE_DATA.reduce((s, r) => s + r.valor, 0);
    const allPageSel = paged.length > 0 && paged.every(r => selected.includes(r.id));
    const selCount = selected.length;

    const toggleAll = () => {
        if (allPageSel) setSelected(s => s.filter(id => !paged.some(r => r.id === id)));
        else setSelected(s => [...new Set([...s, ...paged.map(r => r.id)])]);
    };
    const toggleRow = (id) =>
        setSelected(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id]);

    /* ── Columnas: anchos fijos compactos para que quepan en pantalla ── */
    const COL = {
        check: 36,
        expand: 32,
        instrumento: 0,   /* flex-1 */
        tipo: 140,
        estado: 125,
        region: 80,
        divisa: 65,
        valor: 105,
        acciones: 48,
    };
    const PX = 32; /* padding horizontal del card/filas (pixels) */

    const rowStyle = (isSel) => ({
        display: 'flex',
        alignItems: 'center',
        padding: `7px ${PX}px`,
        gap: 0,
        backgroundColor: isSel ? '#F0FFFE' : 'transparent',
        transition: 'background-color 0.12s',
        cursor: 'default',
    });

    return (
        /* ── Página completa ── */
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, padding: '20px 28px', width: '100%', maxWidth: '1400px', margin: '0 auto' }}>

            {/* ── Encabezado ── */}
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                <div>
                    <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: '#9F9F9F', marginBottom: 4 }}>
                        VALIDACIÓN
                    </p>
                    <h1 style={{ fontSize: 17, fontWeight: 700, color: '#191919', margin: 0 }}>
                        Resultados de Allocations
                    </h1>
                </div>
                <div style={{ textAlign: 'right', paddingLeft: 32, flexShrink: 0 }}>
                    <p style={{ fontSize: 11, color: '#9F9F9F', margin: '0 0 2px' }}>Total validado</p>
                    <p style={{ margin: 0 }}>
                        <span style={{ fontSize: 22, fontWeight: 700, color: '#299D91' }}>
                            {new Intl.NumberFormat('es-AR').format(totalGeneral)}
                        </span>
                        <span style={{ fontSize: 12, color: '#9F9F9F', marginLeft: 4 }}>USD</span>
                    </p>
                </div>
            </div>

            {/* ════════════════════════════════════════
                CARD COMPLETO: Tabs + Toolbar + Tabla + Footer
            ════════════════════════════════════════ */}
            <div style={{ width: '100%', backgroundColor: '#FFFFFF', borderRadius: 16, border: '1px solid #DDE3E6', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)', overflow: 'hidden' }}>

                {/* ── Tabs row ── */}
                <div style={{ display: 'flex', alignItems: 'center', ...borderBottom }}>
                    {TABS.map(tab => {
                        const count = tab === 'Todos' ? SAMPLE_DATA.length : SAMPLE_DATA.filter(r => r.estado === tab).length;
                        const isActive = activeTab === tab;
                        return (
                            <button
                                key={tab}
                                onClick={() => { setActiveTab(tab); setPage(1); }}
                                style={{
                                    display: 'flex', alignItems: 'center', gap: 8,
                                    padding: '8px 18px',
                                    fontSize: 14, fontWeight: 600, cursor: 'pointer',
                                    color: isActive ? '#299D91' : '#71717A',
                                    border: 'none', background: 'transparent',
                                    position: 'relative',
                                }}
                            >
                                {tab}
                                <span style={{
                                    fontSize: 11, fontWeight: 700, padding: '2px 6px', borderRadius: 4,
                                    backgroundColor: isActive ? '#EBF7F6' : '#F3F3F3',
                                    color: isActive ? '#299D91' : '#8E8E93',
                                }}>
                                    {count}
                                </span>
                                {isActive && (
                                    <span style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 2, backgroundColor: '#299D91', borderRadius: '2px 2px 0 0' }} />
                                )}
                            </button>
                        );
                    })}
                </div>

                {/* ── Toolbar ── */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: `8px ${PX}px`, ...borderBottom }}>
                    {/* Filtrar */}
                    <button
                        style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '9px 16px', borderRadius: 12, fontSize: 13, fontWeight: 600, cursor: 'pointer', border: '1px solid #E8E8E8', color: '#525256', backgroundColor: '#FAFAFA', flexShrink: 0, transition: 'border-color 0.15s' }}
                        onMouseEnter={e => { e.currentTarget.style.borderColor = '#299D91'; e.currentTarget.style.color = '#299D91'; }}
                        onMouseLeave={e => { e.currentTarget.style.borderColor = '#E8E8E8'; e.currentTarget.style.color = '#525256'; }}
                    >
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
                        </svg>
                        Filtrar
                    </button>

                    {/* Buscador — crece */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1, padding: '9px 14px', borderRadius: 12, border: '1px solid #E8E8E8', backgroundColor: '#FAFAFA', minWidth: 0 }}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#9F9F9F" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
                            <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
                        </svg>
                        <input
                            type="text" value={search}
                            onChange={e => { setSearch(e.target.value); setPage(1); }}
                            placeholder="Buscar por instrumento, tipo o región…"
                            style={{ flex: 1, border: 'none', outline: 'none', background: 'transparent', fontSize: 13, color: '#191919', minWidth: 0 }}
                        />
                    </div>

                    {/* Acción — no encoge */}
                    <button
                        style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '9px 20px', borderRadius: 12, fontSize: 13, fontWeight: 700, cursor: 'pointer', border: 'none', backgroundColor: '#299D91', color: '#FFFFFF', flexShrink: 0, transition: 'background-color 0.15s' }}
                        onMouseEnter={e => e.currentTarget.style.backgroundColor = '#22857a'}
                        onMouseLeave={e => e.currentTarget.style.backgroundColor = '#299D91'}
                    >
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <polyline points="20 6 9 17 4 12" />
                        </svg>
                        {selCount > 0 ? `Validar (${selCount})` : 'Validar Selección'}
                    </button>
                </div>

                {/* ── Cabecera columnas ── */}
                <div style={{ display: 'flex', alignItems: 'center', padding: `12px ${PX}px`, ...borderBottom, color: '#71717A', fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    <div style={{ width: COL.check, flexShrink: 0, marginRight: 12 }}>
                        <input type="checkbox" checked={allPageSel} onChange={toggleAll} style={{ width: 15, height: 15, cursor: 'pointer', accentColor: '#299D91' }} />
                    </div>
                    <div style={{ width: COL.expand, flexShrink: 0, marginRight: 16 }} />
                    <div style={{ flex: 1, minWidth: 0 }}>Instrumento</div>
                    <div style={{ width: COL.tipo, flexShrink: 0 }}>Tipo</div>
                    <div style={{ width: COL.estado, flexShrink: 0 }}>Estado</div>
                    <div style={{ width: COL.region, flexShrink: 0 }}>Región</div>
                    <div style={{ width: COL.divisa, flexShrink: 0 }}>Divisa</div>
                    <div style={{ width: COL.valor, flexShrink: 0, textAlign: 'right' }}>Valor</div>
                    <div style={{ width: COL.acciones, flexShrink: 0 }} />
                </div>

                {/* ── Filas ── */}
                {paged.length === 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12, padding: '64px 0', color: '#9F9F9F' }}>
                        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                            <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
                        </svg>
                        <p style={{ fontSize: 14, fontWeight: 500 }}>Sin resultados para la búsqueda</p>
                    </div>
                ) : paged.map((row, idx) => {
                    const isSel = selected.includes(row.id);
                    return (
                        <div
                            key={row.id}
                            style={{ ...rowStyle(isSel), ...(idx < paged.length - 1 ? { borderBottom: '1px solid #F5F5F5' } : {}) }}
                            onMouseEnter={e => { if (!isSel) e.currentTarget.style.backgroundColor = '#FAFAFA'; }}
                            onMouseLeave={e => { e.currentTarget.style.backgroundColor = isSel ? '#F0FFFE' : 'transparent'; }}
                        >
                            {/* Checkbox */}
                            <div style={{ width: COL.check, flexShrink: 0, marginRight: 12 }} onClick={() => toggleRow(row.id)}>
                                <input type="checkbox" readOnly checked={isSel} style={{ width: 15, height: 15, cursor: 'pointer', accentColor: '#299D91' }} />
                            </div>

                            {/* Expand */}
                            <div style={{ width: COL.expand, flexShrink: 0, marginRight: 16, color: '#CCCCCC' }}>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                    <circle cx="12" cy="12" r="10" />
                                    <line x1="12" y1="8" x2="12" y2="16" /><line x1="8" y1="12" x2="16" y2="12" />
                                </svg>
                            </div>

                            {/* Instrumento */}
                            <div style={{ flex: 1, minWidth: 0, paddingRight: 16 }}>
                                <p style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#191919', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                    {row.instrumento}
                                </p>
                            </div>

                            {/* Tipo */}
                            <div style={{ width: COL.tipo, flexShrink: 0 }}><TipoPill tipo={row.tipo} /></div>

                            {/* Estado */}
                            <div style={{ width: COL.estado, flexShrink: 0 }}><EstadoPill estado={row.estado} /></div>

                            {/* Región */}
                            <div style={{ width: COL.region, flexShrink: 0, fontSize: 13, color: '#525256' }}>{row.region}</div>

                            {/* Divisa */}
                            <div style={{ width: COL.divisa, flexShrink: 0, fontSize: 13, fontWeight: 500, color: '#878787' }}>{row.divisa}</div>

                            {/* Valor */}
                            <div style={{ width: COL.valor, flexShrink: 0, textAlign: 'right' }}>
                                <span style={{ fontSize: 14, fontWeight: 700, color: '#191919' }}>
                                    {new Intl.NumberFormat('es-AR').format(row.valor)}
                                </span>
                            </div>

                            {/* Tres puntos */}
                            <div style={{ width: COL.acciones, flexShrink: 0, display: 'flex', justifyContent: 'flex-end' }}>
                                <button
                                    style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 32, height: 32, borderRadius: 8, border: 'none', cursor: 'pointer', backgroundColor: 'transparent', color: '#CCCCCC', transition: 'all 0.15s' }}
                                    onMouseEnter={e => { e.currentTarget.style.backgroundColor = '#F3F3F3'; e.currentTarget.style.color = '#525256'; }}
                                    onMouseLeave={e => { e.currentTarget.style.backgroundColor = 'transparent'; e.currentTarget.style.color = '#CCCCCC'; }}
                                >
                                    <DotsIcon />
                                </button>
                            </div>
                        </div>
                    );
                })}

                {/* ── Paginación ── */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: `14px ${PX}px`, ...borderTop }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#9F9F9F' }}>
                        <span>Filas por página:</span>
                        <button style={{ display: 'flex', alignItems: 'center', gap: 4, fontWeight: 600, color: '#525256', background: 'none', border: 'none', cursor: 'pointer' }}>
                            {rowsPerPage}
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                <polyline points="6 9 12 15 18 9" />
                            </svg>
                        </button>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 16, fontSize: 13, color: '#9F9F9F' }}>
                        <span>{(page - 1) * rowsPerPage + 1}–{Math.min(page * rowsPerPage, filtered.length)} de {filtered.length}</span>
                        <div style={{ display: 'flex', gap: 4 }}>
                            {[{ dir: 'prev', pts: '15 18 9 12 15 6' }, { dir: 'next', pts: '9 18 15 12 9 6' }].map(({ dir, pts }) => (
                                <button key={dir}
                                    disabled={dir === 'prev' ? page <= 1 : page >= totalPages}
                                    onClick={() => setPage(p => dir === 'prev' ? p - 1 : p + 1)}
                                    style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 32, height: 32, borderRadius: 8, border: '1px solid #E8E8E8', backgroundColor: '#FAFAFA', color: '#525256', cursor: 'pointer', opacity: (dir === 'prev' ? page <= 1 : page >= totalPages) ? 0.3 : 1, transition: 'opacity 0.15s' }}
                                >
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                        <polyline points={pts} />
                                    </svg>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

            </div>{/* fin card */}
        </div>
    );
}

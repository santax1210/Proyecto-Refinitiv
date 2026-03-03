import { useState, useMemo, useEffect } from 'react';
import { useApp } from '../context/AppContext';

const TABS = ['Todos', 'Balanceado', 'No Balanceado', 'Sin datos'];

const ESTADO_CFG = {
    'Balanceado': { dot: '#299D91', bg: '#EBF7F6', text: '#299D91' },
    'No Balanceado': { dot: '#F0A050', bg: '#FFF7ED', text: '#D97706' },
    'Sin datos': { dot: '#9F9F9F', bg: '#F3F4F6', text: '#71717A' },
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

export default function ValidacionPage({ onNavigate, onSelect }) {
    const { validationData, loadValidationResults, summary } = useApp();
    const [activeTab, setActiveTab] = useState('Todos');
    const [search, setSearch] = useState('');
    const [selected, setSelected] = useState([]);
    const [page, setPage] = useState(1);
    const [showFilterMenu, setShowFilterMenu] = useState(false);
    const [filterEstadoIdx, setFilterEstadoIdx] = useState(null);
    const [loading, setLoading] = useState(false);
    const rowsPerPage = 15;

    // Cargar datos al montar el componente si no están disponibles
    useEffect(() => {
        if (!validationData) {
            setLoading(true);
            loadValidationResults()
                .catch(err => console.error('Error al cargar datos:', err))
                .finally(() => setLoading(false));
        }
    }, [validationData, loadValidationResults]);

    // Usar los datos reales o array vacío si no hay datos
    const SAMPLE_DATA = validationData || [];

    // Filtrado basado en moneda_nueva y Cambio
    const filtered = useMemo(() =>
        SAMPLE_DATA.filter(r => {
            // Filtro por Tab (usa moneda_nueva y Cambio, NO la columna Estado)
            let matchTab = true;
            if (activeTab === 'Balanceado') {
                matchTab = r.moneda_nueva && r.moneda_nueva.toLowerCase() === 'balanceado';
            } else if (activeTab === 'No Balanceado') {
                // Cualquier moneda específica (CLP, USD, EUR, etc.) que NO sea balanceado
                matchTab = r.moneda_nueva && 
                          r.moneda_nueva.toLowerCase() !== 'balanceado' &&
                          r.moneda_nueva.trim() !== '' &&
                          r.Cambio !== 'Sin datos';
            } else if (activeTab === 'Sin datos') {
                matchTab = r.Cambio === 'Sin datos';
            }
            // activeTab === 'Todos' → matchTab = true (todos pasan)

            // Filtro adicional de estado_idx (si se usa dropdown de filtro)
            const matchEstadoIdx = !filterEstadoIdx || (() => {
                if (filterEstadoIdx === 1) return r.moneda_nueva && r.moneda_nueva.toLowerCase() === 'balanceado';
                if (filterEstadoIdx === 2) return r.moneda_nueva && r.moneda_nueva.toLowerCase() !== 'balanceado' && r.Cambio !== 'Sin datos';
                if (filterEstadoIdx === 3) return r.Cambio === 'Sin datos';
                return true;
            })();

            // Filtro de búsqueda
            const matchSearch = !search ||
                (r.Nombre && r.Nombre.toLowerCase().includes(search.toLowerCase())) ||
                (r.ID && r.ID.toString().toLowerCase().includes(search.toLowerCase())) ||
                (r.moneda_antigua && r.moneda_antigua.toLowerCase().includes(search.toLowerCase()));
            
            return matchTab && matchEstadoIdx && matchSearch;
        }), [activeTab, filterEstadoIdx, search, SAMPLE_DATA]);

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
        id_inst: 120,
        estado: 125,
        moneda_antigua: 130,
        pct_antiguo: 110,
        acciones: 48,
    };
    const PX = 32; /* padding horizontal del card/filas (pixels) */

    const rowStyle = (isSel) => ({
        display: 'flex',
        alignItems: 'center',
        padding: `11px ${PX}px`,
        gap: 0,
        backgroundColor: isSel ? '#F0FFFE' : 'transparent',
        transition: 'background-color 0.12s',
        cursor: 'pointer',
    });

    return (
        /* ── Página completa ── */
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, padding: '20px 28px', width: '100%', maxWidth: '1400px', margin: '0 auto' }}>

            {/* ── Mensaje de carga ── */}
            {loading && (
                <div style={{ 
                    display: 'flex', 
                    flexDirection: 'column', 
                    alignItems: 'center', 
                    justifyContent: 'center', 
                    padding: '60px 20px',
                    backgroundColor: '#FFFFFF',
                    borderRadius: 16,
                    border: '1px solid #DDE3E6'
                }}>
                    <div style={{ 
                        width: 40, 
                        height: 40, 
                        border: '3px solid #299D91', 
                        borderTopColor: 'transparent',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite',
                        marginBottom: 16
                    }} />
                    <p style={{ fontSize: 14, fontWeight: 600, color: '#525256', margin: 0 }}>
                        Cargando datos de validación...
                    </p>
                </div>
            )}

            {/* ── Mensaje si no hay datos ── */}
            {!loading && SAMPLE_DATA.length === 0 && (
                <div style={{ 
                    display: 'flex', 
                    flexDirection: 'column', 
                    alignItems: 'center', 
                    justifyContent: 'center', 
                    padding: '60px 20px',
                    backgroundColor: '#FFFFFF',
                    borderRadius: 16,
                    border: '1px solid #DDE3E6',
                    gap: 16
                }}>
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#9F9F9F" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                        <polyline points="14 2 14 8 20 8" />
                        <line x1="12" y1="18" x2="12" y2="12" />
                        <line x1="12" y1="9" x2="12" y2="9" />
                    </svg>
                    <div style={{ textAlign: 'center' }}>
                        <p style={{ fontSize: 16, fontWeight: 700, color: '#191919', margin: 0 }}>
                            No hay datos procesados
                        </p>
                        <p style={{ fontSize: 13, color: '#71717A', margin: '8px 0 0' }}>
                            Subí archivos en la página de Inicio y procesalos para ver los resultados aquí.
                        </p>
                    </div>
                </div>
            )}

            {/* ── Contenido principal (solo si hay datos) ── */}
            {!loading && SAMPLE_DATA.length > 0 && (
                <>

            {/* ── Encabezado ── */}
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                <div>
                    <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: '#9F9F9F', marginBottom: 4 }}>
                        VALIDACIÓN
                    </p>
                    <h1 style={{ fontSize: 20, fontWeight: 700, color: '#191919', margin: 0 }}>
                        Resultados de Allocations
                    </h1>
                </div>
                <div style={{ textAlign: 'right', paddingLeft: 32, flexShrink: 0 }}>
                    <p style={{ fontSize: 11, color: '#9F9F9F', margin: '0 0 2px' }}>Instrumentos</p>
                    <p style={{ margin: 0 }}>
                        <span style={{ fontSize: 22, fontWeight: 700, color: '#299D91' }}>
                            {filtered.length}
                        </span>
                        <span style={{ fontSize: 13, color: '#9F9F9F', marginLeft: 4 }}>
                            / {SAMPLE_DATA.length}
                        </span>
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
                    <div style={{ position: 'relative' }}>
                        <button
                            onClick={() => setShowFilterMenu(!showFilterMenu)}
                            style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '9px 16px', borderRadius: 12, fontSize: 13, fontWeight: 600, cursor: 'pointer', border: `1px solid ${filterEstadoIdx ? '#299D91' : '#E8E8E8'}`, color: filterEstadoIdx ? '#299D91' : '#525256', backgroundColor: filterEstadoIdx ? '#EBF7F6' : '#FAFAFA', transition: 'all 0.15s' }}
                        >
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
                            </svg>
                            {filterEstadoIdx ? `Estado ${filterEstadoIdx}` : 'Filtrar'}
                        </button>

                        {showFilterMenu && (
                            <div style={{ position: 'absolute', top: 'calc(100% + 8px)', left: 0, zIndex: 50, width: 160, backgroundColor: '#FFFFFF', borderRadius: 12, border: '1px solid #DDE3E6', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05)', padding: '6px' }}>
                                {[null, 1, 2, 3].map((val) => (
                                    <button
                                        key={val === null ? 'all' : val}
                                        onClick={() => { setFilterEstadoIdx(val); setShowFilterMenu(false); setPage(1); }}
                                        style={{ display: 'block', width: '100%', padding: '10px 12px', textAlign: 'left', fontSize: 13, fontWeight: filterEstadoIdx === val ? 700 : 500, color: filterEstadoIdx === val ? '#299D91' : '#525256', backgroundColor: filterEstadoIdx === val ? '#F0FFFE' : 'transparent', border: 'none', borderRadius: 6, cursor: 'pointer', transition: 'background-color 0.1s' }}
                                        onMouseEnter={e => { if (filterEstadoIdx !== val) e.currentTarget.style.backgroundColor = '#F9FAFB'; }}
                                        onMouseLeave={e => { if (filterEstadoIdx !== val) e.currentTarget.style.backgroundColor = 'transparent'; }}
                                    >
                                        {val === null ? 'Ver todos' : `Estado ${val}`}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

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
                <div style={{ display: 'flex', alignItems: 'center', padding: `10px ${PX}px`, ...borderBottom, color: '#71717A', fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    <div style={{ width: COL.check, flexShrink: 0, marginRight: 12 }}>
                        <input type="checkbox" checked={allPageSel} onChange={toggleAll} style={{ width: 14, height: 14, cursor: 'pointer', accentColor: '#299D91' }} />
                    </div>
                    <div style={{ width: COL.expand, flexShrink: 0, marginRight: 16 }} />
                    <div style={{ flex: 1, minWidth: 0 }}>Instrumento</div>
                    <div style={{ width: COL.id_inst, flexShrink: 0 }}>ID</div>
                    <div style={{ width: COL.estado, flexShrink: 0 }}>Estado</div>
                    <div style={{ width: COL.moneda_antigua, flexShrink: 0 }}>Moneda Antigua</div>
                    <div style={{ width: COL.pct_antiguo, flexShrink: 0, textAlign: 'right' }}>PCT Antiguo</div>
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
                    const isSel = selected.includes(row.ID);
                    return (
                        <div
                            key={row.ID}
                            style={{ ...rowStyle(isSel), ...(idx < paged.length - 1 ? { borderBottom: '1px solid #F5F5F5' } : {}) }}
                            onMouseEnter={e => { if (!isSel) e.currentTarget.style.backgroundColor = '#E2E8F0'; }}
                            onMouseLeave={e => { e.currentTarget.style.backgroundColor = isSel ? '#F0FFFE' : 'transparent'; }}
                            onClick={() => { onSelect(row.ID); onNavigate('visualizacion'); }}
                        >
                            {/* Checkbox */}
                            <div style={{ width: COL.check, flexShrink: 0, marginRight: 12 }} onClick={(e) => { e.stopPropagation(); toggleRow(row.ID); }}>
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
                                <p style={{ margin: 0, fontSize: 15, fontWeight: 600, color: '#191919', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                    {row.Nombre}
                                </p>
                            </div>

                            {/* ID */}
                            <div style={{ width: COL.id_inst, flexShrink: 0, fontSize: 14, color: '#525256' }}>{row.ID}</div>

                            {/* Estado - Muestra Estado_1, Estado_2, Estado_3 */}
                            <div style={{ width: COL.estado, flexShrink: 0, fontSize: 14, fontWeight: 500, color: '#525256' }}>{row.Estado || ''}</div>

                            {/* Moneda Antigua */}
                            <div style={{ width: COL.moneda_antigua, flexShrink: 0, fontSize: 14, fontWeight: 500, color: '#525256' }}>{row.moneda_antigua || '-'}</div>

                            {/* PCT Antiguo */}
                            <div style={{ width: COL.pct_antiguo, flexShrink: 0, textAlign: 'right' }}>
                                <span style={{ fontSize: 15, fontWeight: 700, color: '#191919' }}>
                                    {row.pct_dominancia_antigua != null ? `${row.pct_dominancia_antigua}%` : '-'}
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

                {/* ── Botones de Generación ── */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 12, padding: `16px ${PX}px`, backgroundColor: '#F9FAFB', ...borderTop }}>
                    <button
                        style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 18px', borderRadius: 10, fontSize: 13, fontWeight: 700, cursor: 'pointer', border: 'none', backgroundColor: '#299D91', color: '#FFFFFF', transition: 'all 0.15s' }}
                        onMouseEnter={e => e.currentTarget.style.backgroundColor = '#22857a'}
                        onMouseLeave={e => e.currentTarget.style.backgroundColor = '#299D91'}
                    >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v4a2 2 0 0 1 2-2" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" />
                        </svg>
                        Generar Balanceado
                    </button>
                    <button
                        style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 18px', borderRadius: 10, fontSize: 13, fontWeight: 700, cursor: 'pointer', border: 'none', backgroundColor: '#F0A050', color: '#FFFFFF', transition: 'all 0.15s' }}
                        onMouseEnter={e => e.currentTarget.style.backgroundColor = '#d98a3d'}
                        onMouseLeave={e => e.currentTarget.style.backgroundColor = '#F0A050'}
                    >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v4a2 2 0 0 1 2-2" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" />
                        </svg>
                        Generar no balanceados
                    </button>
                    <button
                        style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 18px', borderRadius: 10, fontSize: 13, fontWeight: 700, cursor: 'pointer', border: 'none', backgroundColor: '#9F9F9F', color: '#FFFFFF', transition: 'all 0.15s' }}
                        onMouseEnter={e => e.currentTarget.style.backgroundColor = '#8a8a8a'}
                        onMouseLeave={e => e.currentTarget.style.backgroundColor = '#9F9F9F'}
                    >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v4a2 2 0 0 1 2-2" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" />
                        </svg>
                        Generar sin datos
                    </button>
                </div>

            </div>{/* fin card */}
            
            </>
            )}{/* fin contenido principal */}

        </div>
    );
}

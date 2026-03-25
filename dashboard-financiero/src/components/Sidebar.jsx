
import { useState, useRef, useEffect } from 'react';
import { useApp } from '../context/AppContext';

// ─── Inline SVG Icons ───────────────────────────────────────────────────────
const icons = {
    inicio: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" />
            <rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" />
        </svg>
    ),
    validacion: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="5" width="20" height="14" rx="2" /><line x1="2" y1="10" x2="22" y2="10" />
        </svg>
    ),
    visualizacion: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="6" /><circle cx="12" cy="12" r="2" />
        </svg>
    ),
    ajustes: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
        </svg>
    ),
    historial: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
        </svg>
    ),
    logout: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" />
        </svg>
    ),
};

const NAV_ITEMS = [
    { id: 'inicio', label: 'Inicio' },
    { id: 'validacion', label: 'Validacion' },
    { id: 'visualizacion', label: 'Visualizacion' },
    { id: 'historial', label: 'Historial' },
    { id: 'ajustes', label: 'Ajustes' },
];

// ─── Tokens de color del Sidebar ────────────────────────────────────────────
const BG = '#18191B';      // fondo oscuro premium
const TEAL = '#299D91';      // color activo
const TEXT_DIM = '#8A8F98';      // texto inactivo
const TEXT_ON = '#FFFFFF';      // texto activo / hover
const HOVER_BG = 'rgba(255,255,255,0.06)';

const CLASIF_LABELS = { moneda: 'Moneda', region: 'Región', sector: 'Industria' };
const CLASIF_OPCIONES = [
    { key: 'moneda', label: 'Moneda' },
    { key: 'region', label: 'Región' },
    { key: 'sector', label: 'Industria' },
];

// ─── Sidebar Component ───────────────────────────────────────────────────────
export default function Sidebar({ activePage = 'inicio', onNavigate, onLogout }) {
    const { activeClasificacion, setActiveClasificacion, validationDataMap, availableResults } = useApp();
    const clasifLabel = CLASIF_LABELS[activeClasificacion] || null;
    const [dropdownOpen, setDropdownOpen] = useState(false);
    const dropdownRef = useRef(null);

    useEffect(() => {
        if (!dropdownOpen) return;
        const handler = (e) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
                setDropdownOpen(false);
            }
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, [dropdownOpen]);

    return (
        <aside style={{
            display: 'flex', flexDirection: 'column',
            width: 208, flexShrink: 0,
            height: '100%',
            backgroundColor: BG,
            userSelect: 'none',
        }}>
            {/* ── Logo ── */}
            <div style={{ padding: '28px 24px 20px' }}>
                <span style={{ fontSize: 17, letterSpacing: '-0.3px', color: TEXT_ON, fontWeight: 800 }}>
                    Refinitiv <span style={{ color: TEAL }}>Automation</span>
                </span>
                {/* Clasificación activa — selector dropdown */}
                <div style={{ marginTop: 10, position: 'relative' }} ref={dropdownRef}>
                    <button
                        onClick={() => setDropdownOpen(o => !o)}
                        title="Cambiar vista de clasificación"
                        style={{
                            display: 'inline-flex', alignItems: 'center', gap: 6,
                            padding: '3px 9px 3px 9px', borderRadius: 20,
                            backgroundColor: clasifLabel ? 'rgba(41,157,145,0.15)' : 'rgba(255,255,255,0.05)',
                            border: `1px solid ${clasifLabel ? 'rgba(41,157,145,0.30)' : 'rgba(255,255,255,0.08)'}`,
                            cursor: 'pointer',
                            transition: 'opacity 0.15s',
                        }}
                        onMouseEnter={e => { e.currentTarget.style.opacity = '0.8'; }}
                        onMouseLeave={e => { e.currentTarget.style.opacity = '1'; }}
                    >
                        <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: clasifLabel ? TEAL : TEXT_DIM, flexShrink: 0 }} />
                        <span style={{ fontSize: 11, fontWeight: clasifLabel ? 700 : 500, color: clasifLabel ? TEAL : TEXT_DIM, letterSpacing: '0.04em' }}>
                            {clasifLabel || 'Sin clasificación'}
                        </span>
                        {/* chevron */}
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke={clasifLabel ? TEAL : TEXT_DIM} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                            style={{ transition: 'transform 0.15s', transform: dropdownOpen ? 'rotate(180deg)' : 'rotate(0deg)', marginLeft: 1 }}>
                            <polyline points="6 9 12 15 18 9" />
                        </svg>
                    </button>

                    {/* Dropdown menu */}
                    {dropdownOpen && (
                        <div style={{
                            position: 'absolute', top: 'calc(100% + 6px)', left: 0,
                            backgroundColor: '#222426', border: '1px solid rgba(255,255,255,0.1)',
                            borderRadius: 10, overflow: 'hidden',
                            boxShadow: '0 6px 20px rgba(0,0,0,0.4)',
                            zIndex: 1000, minWidth: 130,
                        }}>
                            {CLASIF_OPCIONES.map(({ key, label }) => {
                                const isActive = activeClasificacion === key;
                                const hasData = !!(validationDataMap && validationDataMap[key]) || (availableResults && availableResults.includes(key));
                                return (
                                    <button
                                        key={key}
                                        onClick={() => {
                                            if (hasData || isActive) {
                                                setActiveClasificacion(key);
                                                setDropdownOpen(false);
                                            }
                                        }}
                                        title={!hasData && !isActive ? `Sin datos para ${label}` : undefined}
                                        style={{
                                            display: 'flex', alignItems: 'center', gap: 8,
                                            width: '100%', padding: '9px 14px',
                                            border: 'none', textAlign: 'left',
                                            backgroundColor: isActive ? 'rgba(41,157,145,0.2)' : 'transparent',
                                            color: isActive ? TEAL : hasData ? TEXT_ON : 'rgba(138,143,152,0.4)',
                                            fontSize: 13, fontWeight: isActive ? 700 : 400,
                                            cursor: hasData && !isActive ? 'pointer' : isActive ? 'default' : 'not-allowed',
                                            transition: 'background-color 0.12s',
                                        }}
                                        onMouseEnter={e => { if (hasData && !isActive) e.currentTarget.style.backgroundColor = HOVER_BG; }}
                                        onMouseLeave={e => { if (hasData && !isActive) e.currentTarget.style.backgroundColor = 'transparent'; }}
                                    >
                                        <span style={{ width: 6, height: 6, borderRadius: '50%', flexShrink: 0, backgroundColor: isActive ? TEAL : hasData ? TEXT_DIM : 'rgba(138,143,152,0.25)' }} />
                                        {label}
                                        {isActive && (
                                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ marginLeft: 'auto' }}>
                                                <polyline points="20 6 9 17 4 12" />
                                            </svg>
                                        )}
                                    </button>
                                );
                            })}
                        </div>
                    )}
                </div>
            </div>

            {/* ── Navigation ── */}
            <nav style={{ display: 'flex', flexDirection: 'column', gap: 2, padding: '8px 12px', marginTop: 8 }}>
                {NAV_ITEMS.map((item) => {
                    const isActive = activePage === item.id;
                    return (
                        <button
                            key={item.id}
                            id={`nav-${item.id}`}
                            onClick={() => onNavigate && onNavigate(item.id)}
                            style={{
                                display: 'flex', alignItems: 'center', gap: 14,
                                width: '100%', padding: '11px 16px',
                                borderRadius: 10,
                                border: 'none', cursor: 'pointer',
                                fontSize: 14,
                                fontWeight: isActive ? 700 : 500,
                                backgroundColor: isActive ? TEAL : 'transparent',
                                color: isActive ? TEXT_ON : TEXT_DIM,
                                transition: 'background-color 0.15s, color 0.15s',
                                textAlign: 'left',
                            }}
                            onMouseEnter={e => {
                                if (!isActive) {
                                    e.currentTarget.style.backgroundColor = HOVER_BG;
                                    e.currentTarget.style.color = TEXT_ON;
                                }
                            }}
                            onMouseLeave={e => {
                                if (!isActive) {
                                    e.currentTarget.style.backgroundColor = 'transparent';
                                    e.currentTarget.style.color = TEXT_DIM;
                                }
                            }}
                        >
                            <span style={{ flexShrink: 0, display: 'flex', alignItems: 'center' }}>
                                {icons[item.id]}
                            </span>
                            {item.label}
                        </button>
                    );
                })}
            </nav>

            {/* ── Spacer ── */}
            <div style={{ flex: 1 }} />

            {/* ── Footer ── */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0, paddingBottom: 20 }}>

                {/* Logout */}
                <div style={{ padding: '0 12px 16px' }}>
                    <button
                        id="nav-logout"
                        onClick={() => onLogout && onLogout()}
                        style={{
                            display: 'flex', alignItems: 'center', gap: 12,
                            width: '100%', padding: '10px 16px',
                            borderRadius: 10, border: 'none', cursor: 'pointer',
                            fontSize: 14, fontWeight: 500,
                            backgroundColor: 'rgba(255,255,255,0.05)',
                            color: TEXT_DIM, transition: 'background-color 0.15s, color 0.15s',
                        }}
                        onMouseEnter={e => {
                            e.currentTarget.style.backgroundColor = HOVER_BG;
                            e.currentTarget.style.color = TEXT_ON;
                        }}
                        onMouseLeave={e => {
                            e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.05)';
                            e.currentTarget.style.color = TEXT_DIM;
                        }}
                    >
                        <span style={{ flexShrink: 0, display: 'flex' }}>{icons.logout}</span>
                        Logout
                    </button>
                </div>

                {/* Divider */}
                <div style={{ margin: '0 16px 16px', height: 1, backgroundColor: 'rgba(255,255,255,0.08)' }} />

                {/* User profile */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '0 20px' }}>
                    {/* Avatar */}
                    <div style={{
                        width: 36, height: 36, borderRadius: '50%',
                        backgroundColor: TEAL,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        color: '#FFFFFF', fontSize: 13, fontWeight: 700, flexShrink: 0,
                    }}>
                        SS
                    </div>
                    {/* Name */}
                    <div style={{ flex: 1, minWidth: 0 }}>
                        <p style={{ margin: 0, fontSize: 13, fontWeight: 700, color: TEXT_ON, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            Santiago Salvador
                        </p>
                        <p style={{ margin: 0, fontSize: 11, color: TEXT_DIM, marginTop: 1 }}>
                            Ver perfil
                        </p>
                    </div>
                    {/* Options dots */}
                    <button
                        style={{ flexShrink: 0, background: 'none', border: 'none', cursor: 'pointer', color: TEXT_DIM, padding: 4, transition: 'color 0.15s' }}
                        onMouseEnter={e => e.currentTarget.style.color = TEXT_ON}
                        onMouseLeave={e => e.currentTarget.style.color = TEXT_DIM}
                        aria-label="User options"
                    >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                            <circle cx="12" cy="5" r="2" /><circle cx="12" cy="12" r="2" /><circle cx="12" cy="19" r="2" />
                        </svg>
                    </button>
                </div>
            </div>
        </aside>
    );
}

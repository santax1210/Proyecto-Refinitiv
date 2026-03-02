import { useState } from 'react';

/**
 * FilterDropdown — Dropdown multi-select con el ADN del dashboard.
 * Botón tipo "pill suave" gris cuando inactivo, teal cuando activo/abierto — 
 * consistente con DateFilter pero con lista de opciones expandible.
 */
export default function FilterDropdown({ label = "Filtro", options = [], selectedValues = [], onChange }) {
    const [open, setOpen] = useState(false);
    const hasSelection = selectedValues.length > 0;
    const isActive = open || hasSelection;

    const toggle = (value) => {
        if (selectedValues.includes(value)) {
            onChange(selectedValues.filter(v => v !== value));
        } else {
            onChange([...selectedValues, value]);
        }
    };

    return (
        <div className="relative inline-block">
            {/* ── Trigger button — mismo estilo que DateFilter ── */}
            <button
                onClick={() => setOpen(o => !o)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium cursor-pointer transition-all"
                style={{
                    border: `1px solid ${isActive ? '#299D91' : '#E8E8E8'}`,
                    backgroundColor: isActive ? '#EBF7F6' : '#FAFAFA',
                    color: isActive ? '#299D91' : '#666666',
                }}
                onMouseEnter={e => {
                    if (!isActive) {
                        e.currentTarget.style.backgroundColor = '#F5F5F5';
                    }
                }}
                onMouseLeave={e => {
                    if (!isActive) {
                        e.currentTarget.style.backgroundColor = '#FAFAFA';
                    }
                }}
            >
                {label}
                {hasSelection && (
                    <span
                        className="inline-flex items-center justify-center w-4 h-4 rounded-full text-xs font-bold"
                        style={{ backgroundColor: '#299D91', color: '#FFFFFF' }}
                    >
                        {selectedValues.length}
                    </span>
                )}
                <svg
                    width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                    strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                    style={{ transform: open ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}
                >
                    <polyline points="6 9 12 15 18 9" />
                </svg>
            </button>

            {/* ── Dropdown panel — tarjeta blanca del ADN del dashboard ── */}
            {open && (
                <div
                    className="absolute top-full left-0 mt-2 z-50 rounded-2xl py-2"
                    style={{
                        backgroundColor: '#FFFFFF',
                        border: '1px solid #E8E8E8',
                        minWidth: '200px',
                        boxShadow: '0 8px 24px rgba(0,0,0,0.08)',
                    }}
                >
                    {options.map((opt) => {
                        const checked = selectedValues.includes(opt.value);
                        return (
                            <button
                                key={opt.value}
                                onClick={() => toggle(opt.value)}
                                className="flex items-center gap-3 w-full px-4 py-2.5 text-sm cursor-pointer transition-colors text-left"
                                style={{ color: '#191919' }}
                                onMouseEnter={e => e.currentTarget.style.backgroundColor = '#F8F8F8'}
                                onMouseLeave={e => e.currentTarget.style.backgroundColor = 'transparent'}
                            >
                                {/* Checkbox con teal del ADN */}
                                <span
                                    className="flex items-center justify-center w-4 h-4 rounded shrink-0 transition-all"
                                    style={{
                                        backgroundColor: checked ? '#299D91' : 'transparent',
                                        border: `1.5px solid ${checked ? '#299D91' : '#CCCCCC'}`,
                                    }}
                                >
                                    {checked && (
                                        <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3.5"
                                            strokeLinecap="round" strokeLinejoin="round">
                                            <polyline points="20 6 9 17 4 12" />
                                        </svg>
                                    )}
                                </span>
                                <span>{opt.label}</span>
                            </button>
                        );
                    })}

                    {/* Footer */}
                    <div
                        className="flex items-center justify-between px-4 pt-2 pb-1 mt-1"
                        style={{ borderTop: '1px solid #F0F0F0' }}
                    >
                        <button className="text-xs" style={{ color: '#9F9F9F' }}>+ Mostrar más</button>
                        <button
                            className="text-xs font-semibold cursor-pointer"
                            style={{ color: '#299D91' }}
                            onClick={() => setOpen(false)}
                        >
                            Aplicar
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

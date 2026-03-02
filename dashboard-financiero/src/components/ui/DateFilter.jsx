/**
 * DateFilter — Selector de rango de fechas estilo "pill".
 */
export default function DateFilter({ value, className = "", onClick }) {
    return (
        <button
            onClick={onClick}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium cursor-pointer transition-colors border ${className}`}
            style={{ border: '1px solid #E8E8E8', color: '#666666', backgroundColor: '#FAFAFA' }}
            onMouseEnter={e => e.currentTarget.style.backgroundColor = '#F5F5F5'}
            onMouseLeave={e => e.currentTarget.style.backgroundColor = '#FAFAFA'}
        >
            {value}
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="shrink-0">
                <polyline points="6 9 12 15 18 9" />
            </svg>
        </button>
    );
}

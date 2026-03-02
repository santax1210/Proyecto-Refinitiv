/**
 * SearchBar — Componente de búsqueda global reutilizable.
 */
export default function SearchBar({ placeholder = "Search here", className = "", onChange }) {
    return (
        <div
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl transition-all border ${className}`}
            style={{ backgroundColor: '#F3F3F3', border: '1px solid #E8E8E8' }}
        >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#9F9F9F" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0">
                <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
                type="text"
                placeholder={placeholder}
                onChange={onChange}
                className="bg-transparent outline-none text-sm w-full font-medium"
                style={{ color: '#666666' }}
            />
        </div>
    );
}

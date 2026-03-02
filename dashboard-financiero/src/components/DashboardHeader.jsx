import SearchBar from './ui/SearchBar';

/* ── Header superior del área de contenido ── */
export default function DashboardHeader() {
    return (
        <header
            className="flex items-center justify-between px-8 py-4 bg-white shrink-0"
            style={{ borderBottom: '1px solid #E8E8E8' }}
        >
            {/* Fecha con chevrons */}
            <div className="flex items-center gap-2">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#9F9F9F" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="13 17 18 12 13 7" /><polyline points="6 17 11 12 6 7" />
                </svg>
                <span className="text-sm font-medium" style={{ color: '#878787' }}>May 19, 2023</span>
            </div>

            {/* Notificación + Búsqueda */}
            <div className="flex items-center gap-3">
                {/* Campana */}
                <button
                    id="btn-notifications"
                    className="relative flex items-center justify-center w-9 h-9 rounded-xl cursor-pointer"
                    style={{ backgroundColor: '#F3F3F3' }}
                >
                    <svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor" style={{ color: '#525256' }}>
                        <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z" />
                    </svg>
                    {/* Badge verde */}
                    <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full" style={{ backgroundColor: '#299D91' }} />
                </button>

                {/* Barra de búsqueda (reutilizable) */}
                <SearchBar />
            </div>
        </header>
    );
}

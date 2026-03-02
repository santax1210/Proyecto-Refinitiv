import Button from './ui/Button';

/* ── Sección "Expenses Goals by Category" — grid 3×2 ── */

const CATEGORIES = [
    {
        id: 'housing', label: 'Housing', amount: '$250.00',
        icon: (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#878787" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><polyline points="9 22 9 12 15 12 15 22" />
            </svg>
        ),
    },
    {
        id: 'food', label: 'Food', amount: '$250.00',
        icon: (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#878787" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M18 8h1a4 4 0 0 1 0 8h-1" /><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z" />
                <line x1="6" y1="1" x2="6" y2="4" /><line x1="10" y1="1" x2="10" y2="4" /><line x1="14" y1="1" x2="14" y2="4" />
            </svg>
        ),
    },
    {
        id: 'transportation', label: 'Transportation', amount: '$250.00',
        icon: (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#878787" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="2" y="7" width="20" height="14" rx="2" /><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" />
                <line x1="12" y1="12" x2="12" y2="16" /><line x1="10" y1="14" x2="14" y2="14" />
            </svg>
        ),
    },
    {
        id: 'entertainment', label: 'Entertainment', amount: '$250.00',
        icon: (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#878787" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="23 7 16 12 23 17 23 7" /><rect x="1" y="5" width="15" height="14" rx="2" />
            </svg>
        ),
    },
    {
        id: 'shopping', label: 'Shopping', amount: '$250.00',
        icon: (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#878787" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" /><line x1="3" y1="6" x2="21" y2="6" />
                <path d="M16 10a4 4 0 0 1-8 0" />
            </svg>
        ),
    },
    {
        id: 'others', label: 'Others', amount: '$250.00',
        icon: (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#878787" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" />
                <rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" />
            </svg>
        ),
    },
];

function CategoryCard({ id, label, amount, icon }) {
    return (
        <div
            className="flex items-center justify-between p-5 rounded-2xl bg-white"
            style={{ border: '1px solid #E8E8E8' }}
        >
            {/* Ícono + texto */}
            <div className="flex items-center gap-4">
                <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                    style={{ backgroundColor: '#F3F3F3' }}
                >
                    {icon}
                </div>
                <div>
                    <p className="text-xs font-medium" style={{ color: '#9F9F9F' }}>{label}</p>
                    <p className="text-base font-bold" style={{ color: '#191919' }}>{amount}</p>
                </div>
            </div>

            {/* Botón Adjust (reutilizable) */}
            <Button
                variant="outline"
                id={`btn-adjust-${id}`}
                icon={
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                    </svg>
                }
            >
                Adjust
            </Button>
        </div>
    );
}

export default function CategorySection() {
    return (
        <section className="flex flex-col gap-4">
            <h2 className="text-lg font-bold" style={{ color: '#191919' }}>Expenses Goals by Category</h2>
            <div className="grid grid-cols-3 gap-4">
                {CATEGORIES.map(cat => (
                    <CategoryCard key={cat.id} {...cat} />
                ))}
            </div>
        </section>
    );
}

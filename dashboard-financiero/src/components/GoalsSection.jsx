import DateFilter from './ui/DateFilter';
import Button from './ui/Button';

/* ── Sección "Goals" con dos cards: Savings Goal + Saving Summary ── */

/* Card izquierda: Savings Goal */
function SavingsGoalCard() {
    return (
        <div
            className="flex flex-col gap-5 p-6 rounded-2xl bg-white"
            style={{ border: '1px solid #E8E8E8', width: '300px', flexShrink: 0 }}
        >
            {/* Header de la card */}
            <div className="flex items-center justify-between">
                <span className="font-bold text-base" style={{ color: '#191919' }}>Savings Goal</span>
                {/* Filtro de fecha (reutilizable) */}
                <DateFilter value="01 May ~ 31 May" />
            </div>

            {/* Stats */}
            <div className="flex flex-col gap-4">
                {/* Target Achieved */}
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: '#EBF7F6' }}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#299D91" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <polyline points="20 6 9 17 4 12" />
                        </svg>
                    </div>
                    <div>
                        <p className="text-xs" style={{ color: '#9F9F9F' }}>Target Achieved</p>
                        <p className="text-base font-bold" style={{ color: '#191919' }}>$12,500</p>
                    </div>
                </div>
                {/* This month Target */}
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: '#F3F3F3' }}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#878787" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
                        </svg>
                    </div>
                    <div>
                        <p className="text-xs" style={{ color: '#9F9F9F' }}>This month Target</p>
                        <p className="text-base font-bold" style={{ color: '#191919' }}>$20,000</p>
                    </div>
                </div>
            </div>

            {/* Gauge SVG semicircular */}
            <div className="flex flex-col items-center gap-1">
                {/* Labels de escala */}
                <div className="flex justify-between w-full px-2 mb-1">
                    <span className="text-xs" style={{ color: '#9F9F9F' }}>$0</span>
                    <span className="text-xs" style={{ color: '#9F9F9F' }}>$20k</span>
                </div>
                <svg viewBox="0 0 200 110" width="180" height="100">
                    {/* Arco de fondo (gris) */}
                    <path
                        d="M 20 100 A 80 80 0 0 1 180 100"
                        fill="none" stroke="#E8E8E8" strokeWidth="16" strokeLinecap="round"
                    />
                    {/* Arco de progreso (teal ~62%) */}
                    <path
                        d="M 20 100 A 80 80 0 0 1 180 100"
                        fill="none" stroke="#299D91" strokeWidth="16" strokeLinecap="round"
                        strokeDasharray="251"
                        strokeDashoffset="95"
                    />
                    {/* Aguja / punto indicador */}
                    <circle cx="122" cy="42" r="6" fill="#299D91" />
                    {/* Valor central */}
                    <text x="100" y="88" textAnchor="middle" fontSize="18" fontWeight="700" fill="#191919">12K</text>
                </svg>
                <p className="text-xs text-center" style={{ color: '#9F9F9F' }}>Target vs Achievement</p>
            </div>

            {/* Botón Adjust Goal (reutilizable) */}
            <Button
                variant="outline"
                className="w-full"
                icon={
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                    </svg>
                }
            >
                Adjust Goal
            </Button>
        </div>
    );
}

/* Card derecha: Saving Summary Chart */
function SavingSummaryCard() {
    // Puntos del chart de área (coordenadas SVG 0-600 x 0-200)
    const thisMonth = "M0,140 C30,120 60,80 90,100 C120,120 150,60 180,80 C210,100 240,130 270,90 C300,50 330,110 360,70 C390,30 420,90 450,60 C480,30 510,80 540,50 C570,20 590,60 600,40";
    const lastMonth = "M0,160 C30,150 60,130 90,145 C120,160 150,120 180,135 C210,150 240,140 270,125 C300,110 330,140 360,120 C390,100 420,130 450,110 C480,90 510,120 540,100 C570,80 590,110 600,90";

    const xLabels = ['May 01', 'May 05', 'May 10', 'May 15', 'May 20', 'May 25', 'May 30'];

    return (
        <div
            className="flex flex-col gap-5 p-6 rounded-2xl bg-white flex-1"
            style={{ border: '1px solid #E8E8E8' }}
        >
            {/* Card header */}
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                    <span className="font-bold text-base" style={{ color: '#191919' }}>Saving Summary</span>
                    {/* Filtro de mes (reutilizable) */}
                    <DateFilter value="Mar 2022" />
                </div>
                {/* Leyenda */}
                <div className="flex items-center gap-5">
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#299D91' }} />
                        <span className="text-xs" style={{ color: '#666666' }}>This month</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-1.5 rounded" style={{ backgroundColor: '#D0D0D0' }} />
                        <span className="text-xs" style={{ color: '#666666' }}>Same period last month</span>
                    </div>
                </div>
            </div>

            {/* Chart SVG */}
            <div className="flex gap-3 flex-1 min-h-0">
                {/* Y-axis labels */}
                <div className="flex flex-col justify-between py-1 shrink-0">
                    {['$5000', '$2000', '$500', '$0'].map(l => (
                        <span key={l} className="text-xs" style={{ color: '#9F9F9F' }}>{l}</span>
                    ))}
                </div>

                {/* SVG del chart */}
                <div className="flex-1 flex flex-col gap-2">
                    <svg viewBox="0 0 600 190" preserveAspectRatio="none" className="flex-1 w-full" style={{ minHeight: '140px' }}>
                        <defs>
                            <linearGradient id="gradTeal" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#299D91" stopOpacity="0.25" />
                                <stop offset="100%" stopColor="#299D91" stopOpacity="0.02" />
                            </linearGradient>
                        </defs>
                        {/* Líneas horizontales de guía */}
                        {[18, 72, 126, 175].map(y => (
                            <line key={y} x1="0" y1={y} x2="600" y2={y} stroke="#E8E8E8" strokeWidth="1" />
                        ))}
                        {/* Área rellena teal */}
                        <path d={`${thisMonth} L600,190 L0,190 Z`} fill="url(#gradTeal)" />
                        {/* Línea teal */}
                        <path d={thisMonth} fill="none" stroke="#299D91" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                        {/* Línea gris (mes anterior) */}
                        <path d={lastMonth} fill="none" stroke="#D0D0D0" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="5,3" />
                    </svg>

                    {/* X-axis labels */}
                    <div className="flex justify-between">
                        {xLabels.map(l => (
                            <span key={l} className="text-xs" style={{ color: '#9F9F9F' }}>{l}</span>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

/* Sección Goals completa */
export default function GoalsSection() {
    return (
        <section className="flex flex-col gap-4">
            <h2 className="text-lg font-bold" style={{ color: '#191919' }}>Goals</h2>
            <div className="flex gap-4 items-stretch">
                <SavingsGoalCard />
                <SavingSummaryCard />
            </div>
        </section>
    );
}

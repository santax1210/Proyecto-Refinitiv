import { useRef, useState, useMemo, useEffect, useCallback } from 'react';
import { downloadExport, downloadFilteredExport } from '../services/apiService';
import { useToast } from '../context/ToastContext';

// Formatea strings de pct_dominancia ("CLP 100.00%%" → "CLP 100%", "Technology 85.00%" → "Technology 85%")
function formatPctDominancia(value) {
    if (!value) return '-';
    const match = String(value).match(/^(.+?)\s+([\d\.]+)%*$/);
    if (!match) return value;
    const clase = match[1];
    let pct = parseFloat(match[2]);
    pct = pct % 1 === 0 ? pct.toFixed(0) : pct.toFixed(2).replace(/0+$/, '').replace(/\.$/, '');
    return `${clase} ${pct}%`;
}

// Extrae solo la clase/moneda/región de un string tipo "CLP 100.00%" → "CLP"
function extractClaseFromPct(value) {
    if (!value || typeof value !== 'string' || value.trim() === '' || value === 'Sin datos') return null;
    const match = value.match(/^(.+?)\s+[\d\.]+%*$/);
    return match ? match[1].trim() : null;
}

// Formatea variacion (0-1) como porcentaje (ej: 0.1241 → "12.41%")
function formatVariacion(value) {
    if (value == null) return '-';
    const pct = parseFloat(value) * 100;
    const formatted = pct % 1 === 0 ? pct.toFixed(0) : pct.toFixed(2).replace(/0+$/, '').replace(/\.$/, '');
    return `${formatted}%`;
}

function ExternalLinkIcon() {
    return (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
            <polyline points="15 3 21 3 21 9" />
            <line x1="10" y1="14" x2="21" y2="3" />
        </svg>
    );
}
import { useApp } from '../context/AppContext';

const TABS = ['Todos', 'Balanceado', 'No Balanceado', 'Sin datos'];

// ── Workflow guiado ──────────────────────────────────────────────────────────
const WORKFLOW_STEPS = [
    // Paso 1 · Sin cambios · Baja variación
    {
        paso: 1, sub: 1, tab: 'Balanceado', estadoIdx: 1, variacion: 'Baja',
        label: 'Balanceados · Estado 1 · Baja variación',
        desc: 'Instrumentos ya balanceados, sin cambio de clasificación y con baja variación. Los casos más seguros y directos de validar.'
    },
    {
        paso: 1, sub: 2, tab: 'No Balanceado', estadoIdx: 1, variacion: 'Baja',
        label: 'No Balanceados · Estado 1 · Baja variación',
        desc: 'Instrumentos no balanceados, sin cambio de clasificación y con baja variación. Validación directa y segura.'
    },
    {
        paso: 1, sub: 3, tab: 'Balanceado', estadoIdx: 3, variacion: null,
        label: 'Balanceados · Estado 3',
        desc: 'Instrumentos balanceados con cambios significativos de clasificación. Revisar con atención antes de validar.'
    },
    // Paso 2 · Con cambios · Baja variación
    {
        paso: 2, sub: 1, tab: 'Balanceado', estadoIdx: 2, variacion: 'Baja',
        label: 'Balanceados · Estado 2 · Baja variación',
        desc: 'Instrumentos balanceados con cambio de clasificación y baja variación. Revisar los cambios antes de validar.'
    },
    {
        paso: 2, sub: 2, tab: 'No Balanceado', estadoIdx: 2, variacion: 'Baja',
        label: 'No Balanceados · Estado 2 · Baja variación',
        desc: 'Instrumentos no balanceados con cambio de clasificación y baja variación. Revisar los cambios antes de validar.'
    },
    // Paso 3 · Sin cambios · Alta variación
    {
        paso: 3, sub: 1, tab: 'Balanceado', estadoIdx: 1, variacion: 'Alta',
        label: 'Balanceados · Estado 1 · Alta variación',
        desc: 'Instrumentos balanceados sin cambio de clasificación, pero con alta variación. Pueden existir casos especiales que requieren atención.'
    },
    {
        paso: 3, sub: 2, tab: 'No Balanceado', estadoIdx: 1, variacion: 'Alta',
        label: 'No Balanceados · Estado 1 · Alta variación',
        desc: 'Instrumentos no balanceados sin cambio, pero con alta variación. Revisar en detalle por posibles casos especiales.'
    },
    // Paso 4 · Con cambios · Alta variación
    {
        paso: 4, sub: 1, tab: 'Balanceado', estadoIdx: 2, variacion: 'Alta',
        label: 'Balanceados · Estado 2 · Alta variación',
        desc: 'Instrumentos balanceados con cambio de clasificación y alta variación. Revisión detallada necesaria.'
    },
    {
        paso: 4, sub: 2, tab: 'No Balanceado', estadoIdx: 2, variacion: 'Alta',
        label: 'No Balanceados · Estado 2 · Alta variación',
        desc: 'Instrumentos no balanceados con cambio y alta variación. Mayor complejidad, revisar cada caso individualmente.'
    },
    // Paso 5 · Estado 3 · El caso más crítico
    {
        paso: 5, sub: 1, tab: 'No Balanceado', estadoIdx: 3, variacion: null,
        label: 'No Balanceados · Estado 3',
        desc: 'Los casos más complejos: cambios críticos en instrumentos no balanceados. Revisar cada instrumento individualmente.'
    },
    // Paso 5 · Subpaso hedged: instrumentos con patrón "hedged" en el nombre
    {
        paso: 5, sub: 2, tab: 'Todos', estadoIdx: null, variacion: null, hedged: true,
        label: 'Hedged',
        desc: 'Instrumentos con etiquetas de hedge en el nombre (HEDGE, HEDGED, HDG, etc.). Agrupar para revisión específica.'
    },
];

const PASO_META = [
    { num: 1, title: 'Sin cambios', subtitle: 'Baja variación', color: '#299D91', bg: '#EBF7F6' },
    { num: 2, title: 'Con cambios', subtitle: 'Baja variación', color: '#3B82F6', bg: '#EFF6FF' },
    { num: 3, title: 'Sin cambios', subtitle: 'Alta variación', color: '#F59E0B', bg: '#FFFBEB' },
    { num: 4, title: 'Con cambios', subtitle: 'Alta variación', color: '#F97316', bg: '#FFF7ED' },
    { num: 5, title: 'Estado crítico', subtitle: 'Rev. exhaustiva', color: '#D94A38', bg: '#FFF0EE' },
];

// Patrones para detectar instrumentos hedged en el nombre
const HEDGED_PATTERNS = ['HEDGE', 'HEDGED', '(HEDGED)', 'UNHEDGED', 'HED', 'HDG', '(HDG)'];

function isInstrumentHedged(nombre) {
    if (!nombre) return false;
    const up = String(nombre).toUpperCase();
    return HEDGED_PATTERNS.some(pat => up.includes(pat));
}

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

function AlertaDominanciaIcon({ tipo }) {
    if (!tipo) return null;
    const isDesaparece = tipo === 'DESAPARECE';
    const color = isDesaparece ? '#D97706' : '#D94A38';
    const title = isDesaparece
        ? '\u26a0\ufe0f Desaparece: la categor\u00eda dominante anterior ya no existe en la nueva distribuci\u00f3n'
        : '\uD83D\uDD34 Nueva: esta categor\u00eda dominante no exist\u00eda en la distribuci\u00f3n anterior';
    return (
        <span
            title={title}
            style={{
                flexShrink: 0,
                display: 'inline-flex',
                alignItems: 'center',
                cursor: 'help',
                marginRight: 2,
            }}
        >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
        </span>
    );
}

/* ── Estilos de separador ── */
const borderBottom = { borderBottom: '1px solid #F0F0F0' };
const borderTop = { borderTop: '1px solid #F0F0F0' };


export default function ValidacionPage({ onNavigate, onSelect }) {
    const { validationData, loadValidationResults, summary, activeClasificacion, setActiveClasificacion, validationDataMap, completedPasosMap, updateCompletedPasos } = useApp();
    const toast = useToast();

    const [activeTab, setActiveTab] = useState('Todos');
    const [search, setSearch] = useState('');
    const [selected, setSelected] = useState(() => {
        if (!activeClasificacion) return [];
        try {
            const saved = localStorage.getItem(`allocations_selected_${activeClasificacion}`);
            return saved ? JSON.parse(saved) : [];
        } catch { return []; }
    });
    const [page, setPage] = useState(1);
    const [showFilterMenu, setShowFilterMenu] = useState(false);
    // Filtros por columna PCT
    const [showPctAntiguoMenu, setShowPctAntiguoMenu] = useState(false);
    const [showPctNuevoMenu, setShowPctNuevoMenu] = useState(false);
    const [pctAntiguoFilter, setPctAntiguoFilter] = useState(null); // e.g. 'USD'
    const [pctNuevoFilter, setPctNuevoFilter] = useState(null);
    // Orden en columna Variación: null | 'asc' | 'desc'
    const [variacionSort, setVariacionSort] = useState(null);
    const [filterEstadoIdx, setFilterEstadoIdx] = useState(null);
    const [filterVariacion, setFilterVariacion] = useState(null); // null, 'Baja', 'Alta'
    const [filterRevision, setFilterRevision] = useState(null); // null, 'Validado', 'Rechazado', 'Sin revisar'
    const [revisiones, setRevisiones] = useState({}); // { [ID]: 'Validado' | 'Rechazado' }
    const [loading, setLoading] = useState(false);
    const [downloading, setDownloading] = useState(null); // 'balanceados', 'no_balanceados', 'sin_datos', null
    const [showGlosario, setShowGlosario] = useState(false);
    // Workflow guiado — inicializados directamente desde localStorage (evita race condition de efectos)
    const [workflowMode, setWorkflowMode] = useState(() => {
        if (!activeClasificacion) return true;
        try {
            const v = localStorage.getItem(`allocations_wf_mode_${activeClasificacion}`);
            return v !== 'false';
        } catch { return true; }
    });
    const [workflowSubStepIdx, setWorkflowSubStepIdx] = useState(() => {
        if (!activeClasificacion) return 0;
        try {
            const v = localStorage.getItem(`allocations_wf_step_${activeClasificacion}`);
            const idx = v !== null ? parseInt(v, 10) : 0;
            return !isNaN(idx) ? Math.max(0, Math.min(idx, WORKFLOW_STEPS.length - 1)) : 0;
        } catch { return 0; }
    });
    // completedPasos viene del contexto global — persiste al navegar entre páginas
    const completedPasos = useMemo(
        () => new Set(completedPasosMap[activeClasificacion] || []),
        [completedPasosMap, activeClasificacion]
    );
    const rowsPerPage = 15;

    // Ref siempre actualizado con la clasificación activa — evita que los efectos de
    // persistencia escriban en la clave equivocada al cambiar de clasificación.
    const activeClasifRef = useRef(activeClasificacion);

    // Restaurar filtros y revisiones cuando cambia la clasificación activa
    useEffect(() => {
        activeClasifRef.current = activeClasificacion;
        if (!activeClasificacion) return;

        try {
            const saved = localStorage.getItem(`allocations_filtros_${activeClasificacion}`);
            if (saved) {
                const obj = JSON.parse(saved);
                setActiveTab(obj.activeTab ?? 'Todos');
                setSearch(obj.search ?? '');
                setFilterEstadoIdx(obj.filterEstadoIdx ?? null);
                setFilterVariacion(obj.filterVariacion ?? null);
                setFilterRevision(obj.filterRevision ?? null);
                setPage(obj.page ?? 1);
            } else {
                setActiveTab('Todos'); setSearch('');
                setFilterEstadoIdx(null); setFilterVariacion(null);
                setFilterRevision(null); setPage(1);
            }
        } catch { /* ignorar */ }

        try {
            const savedRev = localStorage.getItem(`allocations_revisiones_${activeClasificacion}`);
            setRevisiones(savedRev ? JSON.parse(savedRev) : {});
        } catch { setRevisiones({}); }

        // Restaurar selección
        try {
            const savedSel = localStorage.getItem(`allocations_selected_${activeClasificacion}`);
            setSelected(savedSel ? JSON.parse(savedSel) : []);
        } catch { setSelected([]); }

        // Restaurar estado del workflow
        try {
            const wfMode = localStorage.getItem(`allocations_wf_mode_${activeClasificacion}`);
            setWorkflowMode(wfMode !== 'false'); // default: true
            const wfStep = localStorage.getItem(`allocations_wf_step_${activeClasificacion}`);
            const idx = wfStep !== null ? parseInt(wfStep, 10) : 0;
            setWorkflowSubStepIdx(!isNaN(idx) ? Math.max(0, Math.min(idx, WORKFLOW_STEPS.length - 1)) : 0);
        } catch {
            setWorkflowMode(true);
            setWorkflowSubStepIdx(0);
        }
    }, [activeClasificacion]);

    // Persistir revisiones cuando cambian (usa ref para clave correcta)
    useEffect(() => {
        if (!activeClasifRef.current) return;
        try {
            localStorage.setItem(`allocations_revisiones_${activeClasifRef.current}`, JSON.stringify(revisiones));
        } catch { /* cuota excedida u otro error, ignorar */ }
    }, [revisiones]);

    // Persistir filtros cuando cambian (usa ref para clave correcta)
    useEffect(() => {
        if (!activeClasifRef.current) return;
        try {
            localStorage.setItem(`allocations_filtros_${activeClasifRef.current}`, JSON.stringify({
                activeTab, search, filterEstadoIdx, filterVariacion, filterRevision, page,
            }));
        } catch { /* cuota excedida u otro error, ignorar */ }
    }, [activeTab, search, filterEstadoIdx, filterVariacion, filterRevision, page]);

    // Cerrar menús PCT al hacer click fuera
    useEffect(() => {
        if (!showPctAntiguoMenu && !showPctNuevoMenu) return;
        const handler = () => {
            setShowPctAntiguoMenu(false);
            setShowPctNuevoMenu(false);
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, [showPctAntiguoMenu, showPctNuevoMenu]);

    // Persistir selección cuando cambia
    useEffect(() => {
        if (!activeClasifRef.current) return;
        try {
            localStorage.setItem(`allocations_selected_${activeClasifRef.current}`, JSON.stringify(selected));
        } catch { /* ignorar */ }
    }, [selected]);

    // Persistir estado del workflow (modo y sub-paso)
    useEffect(() => {
        if (!activeClasifRef.current) return;
        try {
            localStorage.setItem(`allocations_wf_mode_${activeClasifRef.current}`, String(workflowMode));
            localStorage.setItem(`allocations_wf_step_${activeClasifRef.current}`, String(workflowSubStepIdx));
        } catch { /* ignorar */ }
    }, [workflowMode, workflowSubStepIdx]);

    // Cargar datos al montar y cuando cambia la clasificación activa (si no hay datos en memoria)
    useEffect(() => {
        if (!validationData && activeClasificacion) {
            setLoading(true);
            loadValidationResults(activeClasificacion)
                .catch(err => console.error('Error al cargar datos:', err))
                .finally(() => setLoading(false));
        } else if (!validationData && !activeClasificacion) {
            // Sin clasificación activa: intentar cargar la última procesada por el backend
            setLoading(true);
            loadValidationResults(null)
                .catch(err => console.error('Error al cargar datos:', err))
                .finally(() => setLoading(false));
        }
    }, [validationData, loadValidationResults, activeClasificacion]);

    // Usar los datos reales o array vacío si no hay datos
    const SAMPLE_DATA = validationData || [];

    // ── Filtros efectivos según modo (guiado vs. libre) ──────────────────────
    const _wfStep = WORKFLOW_STEPS[workflowSubStepIdx] ?? WORKFLOW_STEPS[0];
    const effTab = workflowMode ? _wfStep.tab : activeTab;
    const effEstadoIdx = workflowMode ? _wfStep.estadoIdx : filterEstadoIdx;
    const effVariacion = workflowMode ? _wfStep.variacion : filterVariacion;

    // Conteos del sub-paso actual para el banner
    const wfStepCounts = useMemo(() => {
        const step = _wfStep;
        const rows = SAMPLE_DATA.filter(r => {
            // Soporte para subpaso especial 'hedged'
            if (step.hedged) {
                return isInstrumentHedged(r.Nombre);
            }
            const cn = r.moneda_nueva ?? r.region_nueva ?? r.sector_nueva;
            let mt = false;
            if (step.tab === 'Balanceado') mt = cn && cn.toLowerCase() === 'balanceado' && r.Cambio !== 'Sin datos';
            else if (step.tab === 'No Balanceado') mt = cn && cn.toLowerCase() !== 'balanceado' && cn.trim() !== '' && r.Cambio !== 'Sin datos';
            const me = step.estadoIdx === 1 ? r.Estado === 'Estado_1'
                : step.estadoIdx === 2 ? r.Estado === 'Estado_2'
                    : step.estadoIdx === 3 ? r.Estado === 'Estado_3' : true;
            const mv = !step.variacion || r.nivel_variacion === step.variacion;
            return mt && me && mv;
        });
        const total = rows.length;
        const validados = rows.filter(r => revisiones[r.ID] === 'Validado').length;
        const rechazados = rows.filter(r => revisiones[r.ID] === 'Rechazado').length;
        return { total, revisados: validados + rechazados, validados, rechazados };
    }, [workflowSubStepIdx, SAMPLE_DATA, revisiones]); // eslint-disable-line

    // Callback para salir del modo guiado (sincroniza los filtros manuales al paso actual)
    const exitWorkflowMode = useCallback((finalizado = false) => {
        if (finalizado) {
            setActiveTab('Balanceado');
            setFilterEstadoIdx(null);
            setFilterVariacion(null);
            setFilterRevision('Validado');
            // Guardar inmediatamente en localStorage para persistencia
            if (activeClasifRef.current) {
                try {
                    localStorage.setItem(`allocations_filtros_${activeClasifRef.current}`, JSON.stringify({
                        activeTab: 'Balanceado',
                        search: '',
                        filterEstadoIdx: null,
                        filterVariacion: null,
                        filterRevision: 'Validado',
                        page: 1,
                    }));
                } catch {/* ignorar */ }
            }
        } else {
            setActiveTab(_wfStep.tab);
            setFilterEstadoIdx(_wfStep.estadoIdx);
            setFilterVariacion(_wfStep.variacion);
        }
        setWorkflowMode(false);
    }, [_wfStep]);

    // Filtrado principal
    const filtered = useMemo(() =>
        SAMPLE_DATA.filter(r => {
            const clasificacionNueva = r.moneda_nueva ?? r.region_nueva ?? r.sector_nueva;
            const clasificacionAntigua = r.moneda_antigua ?? r.region_antigua ?? r.sector_antigua;

            // Si el paso actual es un subpaso 'hedged', filtrar por nombre y omitir otros criterios
            if (workflowMode && _wfStep && _wfStep.hedged) {
                return isInstrumentHedged(r.Nombre);
            }

            // Filtro por Tab (efectivo según modo)
            let matchTab = true;
            if (effTab === 'Balanceado') {
                matchTab = clasificacionNueva && clasificacionNueva.toLowerCase() === 'balanceado' && r.Cambio !== 'Sin datos';
            } else if (effTab === 'No Balanceado') {
                matchTab = clasificacionNueva &&
                    clasificacionNueva.toLowerCase() !== 'balanceado' &&
                    clasificacionNueva.trim() !== '' &&
                    r.Cambio !== 'Sin datos';
            } else if (effTab === 'Sin datos') {
                matchTab = r.Cambio === 'Sin datos';
            }

            // Filtro por Estado (efectivo según modo)
            const matchEstadoIdx = !effEstadoIdx || (() => {
                if (effEstadoIdx === 1) return r.Estado === 'Estado_1';
                if (effEstadoIdx === 2) return r.Estado === 'Estado_2';
                if (effEstadoIdx === 3) return r.Estado === 'Estado_3';
                return true;
            })();

            // Filtro por nivel de variación (efectivo según modo)
            const matchVariacion = !effVariacion || r.nivel_variacion === effVariacion;

            // Filtro por revisión — siempre libre
            const revisionRow = revisiones[r.ID] || 'Sin revisar';
            const matchRevision = !filterRevision || revisionRow === filterRevision;

            // Búsqueda — siempre libre
            const matchSearch = !search ||
                (r.Nombre && r.Nombre.toLowerCase().includes(search.toLowerCase())) ||
                (r.ID && r.ID.toString().toLowerCase().includes(search.toLowerCase())) ||
                (clasificacionAntigua && clasificacionAntigua.toLowerCase().includes(search.toLowerCase()));

            // Filtro por columna PCT Antiguo/Nuevo: extrae la clase del string "CLP 100%" → "CLP"
            const claseAntigua = extractClaseFromPct(r.pct_dominancia_antigua);
            const claseNueva = extractClaseFromPct(r.pct_dominancia_nuevo ?? r.pct_dominancia_nueva);
            const matchPctAnt = !pctAntiguoFilter || claseAntigua === pctAntiguoFilter;
            const matchPctNue = !pctNuevoFilter || claseNueva === pctNuevoFilter;

            return matchTab && matchEstadoIdx && matchVariacion && matchRevision && matchSearch && matchPctAnt && matchPctNue;
        }), [effTab, effEstadoIdx, effVariacion, filterRevision, revisiones, search, pctAntiguoFilter, pctNuevoFilter, SAMPLE_DATA]); // eslint-disable-line

    // Aplicar ordenamiento por columna Variación sobre el conjunto filtrado
    // Usa los mismos campos que muestra la columna: variacion_balanceados ?? variacion_no_balanceados
    const sorted = useMemo(() => {
        if (!variacionSort) return filtered;
        const copy = [...filtered];
        copy.sort((a, b) => {
            const va = parseFloat(a.variacion_balanceados ?? a.variacion_no_balanceados ?? null);
            const vb = parseFloat(b.variacion_balanceados ?? b.variacion_no_balanceados ?? null);
            if (isNaN(va) && isNaN(vb)) return 0;
            if (isNaN(va)) return 1;  // sin variación va al final siempre
            if (isNaN(vb)) return -1;
            return variacionSort === 'asc' ? va - vb : vb - va;
        });
        return copy;
    }, [filtered, variacionSort]);

    // Valores únicos para los filtros por columna
    // Extrae la clase directamente del campo pct_dominancia_* (igual que lo que se muestra en la celda)
    const uniqueAntiguas = useMemo(() => {
        const s = new Set();
        SAMPLE_DATA.forEach(r => {
            const clase = extractClaseFromPct(r.pct_dominancia_antigua);
            if (clase) s.add(clase);
        });
        return Array.from(s).sort();
    }, [SAMPLE_DATA]);
    const uniqueNuevas = useMemo(() => {
        const s = new Set();
        SAMPLE_DATA.forEach(r => {
            const clase = extractClaseFromPct(r.pct_dominancia_nuevo ?? r.pct_dominancia_nueva);
            if (clase) s.add(clase);
        });
        return Array.from(s).sort();
    }, [SAMPLE_DATA]);

    const totalPages = Math.ceil(sorted.length / rowsPerPage);
    const paged = sorted.slice((page - 1) * rowsPerPage, page * rowsPerPage);
    const totalGeneral = SAMPLE_DATA.reduce((s, r) => s + r.valor, 0);
    const allPageSel = paged.length > 0 && paged.every(r => selected.includes(r.id));
    const selCount = selected.length;
    const filterKey = `${effTab}|${search}|${effEstadoIdx ?? ''}|${effVariacion ?? ''}|${filterRevision ?? ''}|${pctAntiguoFilter ?? ''}|${pctNuevoFilter ?? ''}|${variacionSort ?? ''}|${page}`;

    const toggleAll = () => {
        if (allPageSel) setSelected(s => s.filter(id => !paged.some(r => r.id === id)));
        else setSelected(s => [...new Set([...s, ...paged.map(r => r.id)])]);
    };

    // Toggle selección y validación
    const toggleRow = (id) => {
        setSelected(s => {
            const isSel = s.includes(id);
            const isValidado = revisiones[id] === 'Validado';
            // El checkbox aparece marcado si está seleccionado O validado
            const appearsChecked = isSel || isValidado;
            if (appearsChecked) {
                // Desmarcar: sacar de selección y quitar validación si la tenía
                if (isValidado) {
                    setRevisiones(prev => {
                        const next = { ...prev };
                        next[id] = 'Sin revisar';
                        return next;
                    });
                }
                return s.filter(x => x !== id);
            } else {
                return [...s, id];
            }
        });
    };


    const handleValidar = () => {
        if (selected.length === 0) return;
        const count = selected.length;
        setRevisiones(prev => {
            const next = { ...prev };
            selected.forEach(id => { next[id] = 'Validado'; });
            return next;
        });
        setSelected([]);
        toast({ message: `${count} instrumento${count !== 1 ? 's' : ''} validado${count !== 1 ? 's' : ''} correctamente`, type: 'success' });
    };

    // Validar todos los instrumentos filtrados que no estén ya validados
    const handleValidarTodosFiltrados = () => {
        const idsToValidate = filtered.filter(r => (revisiones[r.ID] !== 'Validado')).map(r => r.ID);
        if (idsToValidate.length === 0) return;
        const count = idsToValidate.length;
        setRevisiones(prev => {
            const next = { ...prev };
            idsToValidate.forEach(id => { next[id] = 'Validado'; });
            return next;
        });
        // Si alguno estaba seleccionado, los quitamos de la selección
        setSelected(sel => sel.filter(id => !idsToValidate.includes(id)));
        toast({ message: `${count} instrumento${count !== 1 ? 's' : ''} validado${count !== 1 ? 's' : ''} masivamente`, type: 'success', duration: 5000 });
    };

    const handleRechazar = () => {
        if (selected.length === 0) return;
        const count = selected.length;
        setRevisiones(prev => {
            const next = { ...prev };
            selected.forEach(id => { next[id] = 'Rechazado'; });
            return next;
        });
        setSelected([]);
        toast({ message: `${count} instrumento${count !== 1 ? 's' : ''} rechazado${count !== 1 ? 's' : ''}`, type: 'warning' });
    };

    // Manejar descarga de exports
    const handleDownload = async (exportType) => {
        try {
            setDownloading(exportType);
            const filteredIds = filtered.map(row => row.ID);
            if (filteredIds.length < SAMPLE_DATA.length) {
                await downloadFilteredExport(exportType, filteredIds);
            } else {
                await downloadExport(exportType);
            }
            toast({ message: `Archivo "${exportType.replace(/_/g, ' ')}" descargado correctamente`, type: 'success' });
        } catch (error) {
            // Mostrar error detallado en toast
            let errorMsg = error.message || 'Error desconocido al descargar export.';
            if (error.stack) {
                errorMsg += '\n' + error.stack.split('\n')[0];
            }
            toast({ message: `Error al descargar export: ${errorMsg}`, type: 'error', duration: 7000 });
            console.error('Error al descargar export:', error);
        } finally {
            setDownloading(null);
        }
    };

    /* ── Columnas: anchos fijos compactos para que quepan en pantalla ── */
    const COL = {
        check: 36,
        expand: 32,
        instrumento: 0,   /* flex-1 */
        id_inst: 120,
        estado: 125,
        pct_antiguo: 110,
        pct_nuevo: 110,
        variacion: 100,
        acciones: 48,
    };
    const PX = 32; /* padding horizontal del card/filas (pixels) */

    const rowStyle = (isSel, revision) => ({
        display: 'flex',
        alignItems: 'center',
        padding: `11px ${PX}px`,
        gap: 0,
        backgroundColor: revision === 'Validado' ? '#E9F9F7' : revision === 'Rechazado' ? '#FFF0EE' : isSel ? '#F0FFFE' : 'transparent',
        transition: 'background-color 0.12s',
        cursor: 'pointer',
    });

    return (
        /* ── Página completa ── */
        <div className="anim-fade-slide" style={{ display: 'flex', flexDirection: 'column', gap: 14, padding: '20px 28px', width: '100%', maxWidth: '1400px', margin: '0 auto' }}>
            {/* Modal Glosario */}
            {showGlosario && (
                <div
                    onClick={() => setShowGlosario(false)}
                    style={{ position: 'fixed', inset: 0, zIndex: 200, backgroundColor: 'rgba(0,0,0,0.35)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                >
                    <div
                        onClick={e => e.stopPropagation()}
                        style={{ background: '#FFFFFF', borderRadius: 16, padding: '28px 32px', width: 560, maxWidth: '92vw', boxShadow: '0 20px 40px rgba(0,0,0,0.18)', position: 'relative' }}
                    >
                        {/* Cerrar */}
                        <button onClick={() => setShowGlosario(false)} style={{ position: 'absolute', top: 16, right: 16, width: 28, height: 28, borderRadius: 8, border: 'none', backgroundColor: '#F3F4F6', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#71717A' }}
                            onMouseEnter={e => e.currentTarget.style.backgroundColor = '#E5E7EB'}
                            onMouseLeave={e => e.currentTarget.style.backgroundColor = '#F3F4F6'}
                        >
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
                        </button>
                        <h3 style={{ fontSize: 16, fontWeight: 700, margin: '0 0 18px', color: '#191919' }}>Glosario de Estados</h3>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 28px' }}>
                            {/* Balanceados */}
                            <div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
                                    <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#299D91', flexShrink: 0 }} />
                                    <span style={{ fontWeight: 700, fontSize: 13, color: '#299D91' }}>Balanceados</span>
                                </div>
                                {[
                                    { estado: 'Estado 1', titulo: 'Balanceado → Balanceado', desc: 'El instrumento ya estaba balanceado y sigue balanceado.' },
                                    { estado: 'Estado 2', titulo: 'Moneda → Balanceado', desc: 'Tenía una moneda dominante y ahora está balanceado.' },
                                    { estado: 'Estado 3', titulo: 'Falta Allocation', desc: 'No se encontró allocation suficiente para balancear.' },
                                ].map(({ estado, titulo, desc }) => (
                                    <div key={estado} style={{ marginBottom: 12, paddingLeft: 14, borderLeft: '2px solid #C5EDE9' }}>
                                        <div style={{ fontSize: 12, fontWeight: 700, color: '#299D91', marginBottom: 1 }}>{estado}</div>
                                        <div style={{ fontSize: 13, fontWeight: 600, color: '#191919' }}>{titulo}</div>
                                        <div style={{ fontSize: 11, color: '#71717A', marginTop: 1 }}>{desc}</div>
                                    </div>
                                ))}
                            </div>
                            {/* No Balanceados */}
                            <div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
                                    <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#F0A050', flexShrink: 0 }} />
                                    <span style={{ fontWeight: 700, fontSize: 13, color: '#D97706' }}>No Balanceados</span>
                                </div>
                                {[
                                    { estado: 'Estado 1', titulo: 'Moneda → Misma Moneda', desc: 'Ej: USD → USD. No hubo cambio de moneda dominante.' },
                                    { estado: 'Estado 2', titulo: 'Balanceado → Moneda', desc: 'Estaba balanceado y ahora tiene una moneda dominante.' },
                                    { estado: 'Estado 3', titulo: 'Moneda → Otra Moneda', desc: 'Ej: USD → EUR. Cambió la moneda dominante.' },
                                ].map(({ estado, titulo, desc }) => (
                                    <div key={estado} style={{ marginBottom: 12, paddingLeft: 14, borderLeft: '2px solid #FFD9A8' }}>
                                        <div style={{ fontSize: 12, fontWeight: 700, color: '#D97706', marginBottom: 1 }}>{estado}</div>
                                        <div style={{ fontSize: 13, fontWeight: 600, color: '#191919' }}>{titulo}</div>
                                        <div style={{ fontSize: 11, color: '#71717A', marginTop: 1 }}>{desc}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* ── Skeleton de carga ── */}
            {loading && (
                <div style={{ backgroundColor: '#FFFFFF', borderRadius: 16, border: '1px solid #DDE3E6', overflow: 'hidden' }}>
                    {/* Tabs skeleton */}
                    <div style={{ display: 'flex', gap: 16, padding: '12px 32px', borderBottom: '1px solid #F0F0F0' }}>
                        {[80, 90, 100, 75].map((w, i) => (
                            <div key={i} className="skeleton" style={{ height: 24, width: w, borderRadius: 6 }} />
                        ))}
                    </div>
                    {/* Toolbar skeleton */}
                    <div style={{ display: 'flex', gap: 12, padding: '10px 32px', borderBottom: '1px solid #F0F0F0', alignItems: 'center' }}>
                        <div className="skeleton" style={{ height: 34, width: 110, borderRadius: 12 }} />
                        <div className="skeleton" style={{ height: 34, flex: 1, borderRadius: 12 }} />
                        <div className="skeleton" style={{ height: 34, width: 100, borderRadius: 12 }} />
                        <div className="skeleton" style={{ height: 34, width: 108, borderRadius: 12 }} />
                    </div>
                    {/* Header skeleton */}
                    <div style={{ display: 'flex', gap: 16, padding: '10px 32px', borderBottom: '1px solid #F0F0F0' }}>
                        {[16, 120, 80, 125, 110, 110, 100].map((w, i) => (
                            <div key={i} className="skeleton" style={{ height: 12, width: w, flexShrink: 0 }} />
                        ))}
                    </div>
                    {/* Row skeletons */}
                    {[...Array(8)].map((_, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '13px 32px', borderBottom: '1px solid #F8F8F8' }}>
                            <div className="skeleton" style={{ width: 16, height: 16, borderRadius: 3, flexShrink: 0 }} />
                            <div className="skeleton" style={{ width: 22, height: 22, borderRadius: 4, flexShrink: 0 }} />
                            <div className="skeleton" style={{ flex: 1, height: 14, minWidth: 0 }} />
                            <div className="skeleton" style={{ width: 120, height: 14, flexShrink: 0 }} />
                            <div className="skeleton" style={{ width: 100, height: 22, borderRadius: 999, flexShrink: 0 }} />
                            <div className="skeleton" style={{ width: 80, height: 14, flexShrink: 0 }} />
                            <div className="skeleton" style={{ width: 80, height: 14, flexShrink: 0 }} />
                            <div className="skeleton" style={{ width: 80, height: 14, flexShrink: 0 }} />
                        </div>
                    ))}
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

                    {/* ════════════════════════════════════════════════════
                BARRA WIZARD: 5 pasos de validación
            ════════════════════════════════════════════════════ */}
                    {(() => {
                        // Un paso está completo si el usuario presionó Siguiente para avanzar más allá de él
                        const isPasoCompleto = (pasoNum) => completedPasos.has(pasoNum);

                        return (
                            <div style={{ backgroundColor: '#FFFFFF', borderRadius: 10, border: '1px solid #DDE3E6', padding: '8px 14px 4px 14px', boxShadow: '0 2px 4px rgba(0,0,0,0.04)', marginBottom: 8 }}>
                                {/* Título + toggle modo libre */}
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                                    <div>
                                        <p style={{ margin: 0, fontSize: 10, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#9F9F9F' }}>Flujo de Validación</p>
                                        {/* Línea de subpaso eliminada para mayor simpleza visual */}
                                        {!workflowMode && (
                                            <p style={{ margin: '2px 0 0', fontSize: 12, color: '#525256' }}>Modo libre activo — filtrá manualmente</p>
                                        )}
                                    </div>
                                    <button
                                        onClick={() => {
                                            if (workflowMode) {
                                                exitWorkflowMode();
                                            } else {
                                                setWorkflowMode(true);
                                            }
                                        }}
                                        style={{
                                            display: 'flex', alignItems: 'center', gap: 6,
                                            padding: '6px 14px', borderRadius: 20,
                                            border: `1.5px solid ${workflowMode ? '#DDE3E6' : '#299D91'}`,
                                            backgroundColor: workflowMode ? '#F8FAFC' : '#EBF7F6',
                                            color: workflowMode ? '#71717A' : '#299D91',
                                            fontSize: 12, fontWeight: 600, cursor: 'pointer', transition: 'all 0.15s',
                                        }}
                                        onMouseEnter={e => { e.currentTarget.style.opacity = '0.8'; }}
                                        onMouseLeave={e => { e.currentTarget.style.opacity = '1'; }}
                                    >
                                        {workflowMode ? (
                                            <>
                                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
                                                Modo libre
                                            </>
                                        ) : (
                                            <>
                                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12a9 9 0 1 0 18 0 9 9 0 0 0-18 0" /><polyline points="12 8 12 12 14 14" /></svg>
                                                Volver al flujo
                                            </>
                                        )}
                                    </button>
                                </div>

                                {/* Pasos */}
                                <div style={{ display: 'flex', alignItems: 'center', gap: 0, minHeight: 0 }}>
                                    {PASO_META.map((meta, i) => {
                                        const isActive = workflowMode && _wfStep.paso === meta.num;
                                        const isCompleto = isPasoCompleto(meta.num);
                                        const isFuturo = workflowMode && _wfStep.paso < meta.num && !isCompleto;
                                        const firstSubIdx = WORKFLOW_STEPS.findIndex(s => s.paso === meta.num);

                                        return (
                                            <div key={meta.num} style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                                                {/* Conector izquierdo */}
                                                {i > 0 && (
                                                    <div style={{
                                                        flex: 1, height: 2,
                                                        backgroundColor: isPasoCompleto(PASO_META[i - 1].num) ? '#299D91' : '#E5E7EB',
                                                        transition: 'background-color 0.3s',
                                                    }} />
                                                )}

                                                {/* Nodo del paso */}
                                                <button
                                                    onClick={() => {
                                                        setWorkflowSubStepIdx(firstSubIdx);
                                                        setWorkflowMode(true);
                                                        setPage(1);
                                                    }}
                                                    title={`Ir al Paso ${meta.num}: ${meta.title}`}
                                                    style={{
                                                        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3,
                                                        background: 'none', border: 'none', cursor: 'pointer', padding: '0 4px',
                                                        flexShrink: 0,
                                                    }}
                                                >
                                                    {/* Círculo numerado */}
                                                    <div style={{
                                                        width: 22, height: 22, borderRadius: '50%',
                                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                        backgroundColor: isCompleto ? '#299D91' : isActive ? meta.color : '#F3F4F6',
                                                        border: `2px solid ${isCompleto ? '#299D91' : isActive ? meta.color : isFuturo ? '#E5E7EB' : '#DDE3E6'}`,
                                                        color: isCompleto || isActive ? '#FFFFFF' : '#9F9F9F',
                                                        fontSize: 11, fontWeight: 700,
                                                        boxShadow: isActive ? `0 0 0 2px ${meta.bg}` : 'none',
                                                        transition: 'all 0.2s',
                                                    }}>
                                                        {isCompleto
                                                            ? <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
                                                            : meta.num
                                                        }
                                                    </div>
                                                    {/* Etiqueta */}
                                                    <div style={{ textAlign: 'center' }}>
                                                        <div style={{ fontSize: 9.5, fontWeight: 700, color: isActive ? meta.color : isCompleto ? '#299D91' : '#9F9F9F', whiteSpace: 'nowrap' }}>
                                                            {meta.title}
                                                        </div>
                                                        <div style={{ fontSize: 8.5, color: '#B0B0B0', whiteSpace: 'nowrap' }}>
                                                            {meta.subtitle}
                                                        </div>
                                                    </div>
                                                </button>

                                                {/* Conector derecho (solo en último nodo a la derecha) */}
                                                {i < PASO_META.length - 1 && (
                                                    <div style={{
                                                        flex: 1, height: 2,
                                                        backgroundColor: isCompleto ? '#299D91' : '#E5E7EB',
                                                        transition: 'background-color 0.3s',
                                                    }} />
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        );
                    })()}

                    {/* ── Encabezado ── */}
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                                <div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                                        <h1 style={{ fontSize: 20, fontWeight: 700, color: '#191919', margin: 0 }}>
                                            Tabla Validacion
                                        </h1>
                                        {/* Contador de validados por filtro activo */}
                                        {(() => {
                                            let tabRows = [];
                                            if (effTab === 'Todos') {
                                                tabRows = SAMPLE_DATA;
                                            } else if (effTab === 'Balanceado') {
                                                tabRows = SAMPLE_DATA.filter(r => {
                                                    const clasificacionNueva = r.moneda_nueva ?? r.region_nueva ?? r.sector_nueva;
                                                    return clasificacionNueva && clasificacionNueva.toLowerCase() === 'balanceado' && r.Cambio !== 'Sin datos';
                                                });
                                            } else if (effTab === 'No Balanceado') {
                                                tabRows = SAMPLE_DATA.filter(r => {
                                                    const clasificacionNueva = r.moneda_nueva ?? r.region_nueva ?? r.sector_nueva;
                                                    return clasificacionNueva && clasificacionNueva.toLowerCase() !== 'balanceado' && clasificacionNueva.trim() !== '' && r.Cambio !== 'Sin datos';
                                                });
                                            } else if (effTab === 'Sin datos') {
                                                tabRows = SAMPLE_DATA.filter(r => r.Cambio === 'Sin datos');
                                            }
                                            const validadosTab = tabRows.filter(r => revisiones[r.ID] === 'Validado').length;
                                            return (
                                                <span style={{
                                                    display: 'inline-flex', alignItems: 'center', gap: 5,
                                                    fontSize: 13, fontWeight: 700, color: '#299D91',
                                                    background: '#EBF7F6', borderRadius: 8, padding: '3px 12px',
                                                    marginLeft: 2
                                                }}
                                                    title={`Instrumentos validados en "${effTab}"`}
                                                >
                                                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#299D91" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 2 }}>
                                                        <polyline points="20 6 9 17 4 12" />
                                                    </svg>
                                                    {validadosTab} validados
                                                </span>
                                            );
                                        })()}
                                    </div>
                                </div>
                                {/* Botón helper glosario */}
                                <button
                                    onClick={() => setShowGlosario(true)}
                                    title="Ver glosario de estados"
                                    style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 26, height: 26, borderRadius: '50%', border: '1.5px solid #DDE3E6', backgroundColor: '#F8FAFC', color: '#9F9F9F', cursor: 'pointer', fontSize: 13, fontWeight: 700, flexShrink: 0, transition: 'all 0.15s', marginTop: 16 }}
                                    onMouseEnter={e => { e.currentTarget.style.backgroundColor = '#EBF7F6'; e.currentTarget.style.borderColor = '#299D91'; e.currentTarget.style.color = '#299D91'; }}
                                    onMouseLeave={e => { e.currentTarget.style.backgroundColor = '#F8FAFC'; e.currentTarget.style.borderColor = '#DDE3E6'; e.currentTarget.style.color = '#9F9F9F'; }}
                                >?
                                </button>
                            </div>
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
                    <div className="card-hover" style={{ width: '100%', backgroundColor: '#FFFFFF', borderRadius: 16, border: '1px solid #DDE3E6', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)', overflow: 'hidden' }}>

                        {/* ── Tabs row ── */}
                        <div style={{ display: 'flex', alignItems: 'center', ...borderBottom }}>
                            {TABS.map(tab => {
                                // Filtrar instrumentos por tab
                                let tabRows = [];
                                if (tab === 'Todos') {
                                    tabRows = SAMPLE_DATA;
                                } else if (tab === 'Balanceado') {
                                    tabRows = SAMPLE_DATA.filter(r => {
                                        const clasificacionNueva = r.moneda_nueva ?? r.region_nueva ?? r.sector_nueva;
                                        return clasificacionNueva && clasificacionNueva.toLowerCase() === 'balanceado' && r.Cambio !== 'Sin datos';
                                    });
                                } else if (tab === 'No Balanceado') {
                                    tabRows = SAMPLE_DATA.filter(r => {
                                        const clasificacionNueva = r.moneda_nueva ?? r.region_nueva ?? r.sector_nueva;
                                        return clasificacionNueva && clasificacionNueva.toLowerCase() !== 'balanceado' && clasificacionNueva.trim() !== '' && r.Cambio !== 'Sin datos';
                                    });
                                } else if (tab === 'Sin datos') {
                                    tabRows = SAMPLE_DATA.filter(r => r.Cambio === 'Sin datos');
                                }
                                const count = tabRows.length;
                                // En modo guiado la tab activa la dicta el workflow (effTab)
                                const isActive = workflowMode ? effTab === tab : activeTab === tab;
                                // En modo guiado las tabs Todos/Sin datos no son relevantes — baja opacidad
                                const isIrrelevant = workflowMode && (tab === 'Todos' || tab === 'Sin datos');
                                return (
                                    <button
                                        key={tab}
                                        onClick={() => {
                                            if (workflowMode) return; // en modo guiado las tabs no son clicables
                                            setActiveTab(tab); setPage(1);
                                        }}
                                        title={workflowMode ? 'Las tabs son gestionadas por el flujo guiado. Usá "Modo libre" para filtrar manualmente.' : tab}
                                        style={{
                                            display: 'flex', alignItems: 'center', gap: 8,
                                            padding: '8px 18px',
                                            fontSize: 14, fontWeight: 600,
                                            cursor: workflowMode ? 'default' : 'pointer',
                                            color: isActive ? '#299D91' : '#71717A',
                                            border: 'none', background: 'transparent',
                                            position: 'relative',
                                            opacity: isIrrelevant ? 0.35 : 1,
                                            transition: 'opacity 0.2s',
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

                        {/* ── Banner del sub-paso (solo en modo guiado) ── */}
                        {workflowMode && (() => {
                            const step = _wfStep;
                            const meta = PASO_META[step.paso - 1];
                            const { total, revisados, validados, rechazados } = wfStepCounts;
                            const pct = total > 0 ? Math.round((revisados / total) * 100) : 0;
                            const allDone = total > 0 && revisados === total;
                            const isLast = workflowSubStepIdx === WORKFLOW_STEPS.length - 1;
                            const subTotalInPaso = WORKFLOW_STEPS.filter(s => s.paso === step.paso).length;
                            const isLastSubInPaso = step.sub === subTotalInPaso;

                            return (
                                <div style={{
                                    margin: `0 ${PX}px`,
                                    marginTop: 10,
                                    marginBottom: 2,
                                    borderRadius: 12,
                                    border: `1.5px solid ${allDone ? '#299D91' : meta.color + '40'}`,
                                    backgroundColor: allDone ? '#EBF7F6' : meta.bg,
                                    padding: '12px 16px',
                                    transition: 'all 0.2s',
                                }}>
                                    {/* Fila superior: info + navegación */}
                                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
                                        {/* Indicador paso · sub-paso + descripción */}
                                        <div style={{ flex: 1, minWidth: 0 }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                                                <span style={{
                                                    fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 6,
                                                    backgroundColor: allDone ? '#299D91' : meta.color,
                                                    color: '#FFFFFF',
                                                }}>
                                                    Paso {step.paso} · {step.sub}/{subTotalInPaso}
                                                </span>
                                                {/* Dots sub-paso */}
                                                <div style={{ display: 'flex', gap: 4 }}>
                                                    {Array.from({ length: subTotalInPaso }, (_, i) => i + 1).map(s => (
                                                        <span key={s} style={{
                                                            width: 7, height: 7, borderRadius: '50%',
                                                            backgroundColor: s === step.sub ? (allDone ? '#299D91' : meta.color) : '#DDE3E6',
                                                            transition: 'background-color 0.2s',
                                                        }} />
                                                    ))}
                                                </div>
                                                {allDone && (
                                                    <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, fontWeight: 700, color: '#299D91' }}>
                                                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#299D91" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
                                                        Sub-paso completado
                                                    </span>
                                                )}
                                            </div>
                                            <p style={{ margin: 0, fontSize: 12, fontWeight: 600, color: '#191919' }}>
                                                {step.label}
                                            </p>
                                            <p style={{ margin: '2px 0 0', fontSize: 11, color: '#71717A' }}>
                                                {step.desc}
                                            </p>
                                        </div>
                                        {/* Navegación anterior / siguiente */}
                                        <div style={{ display: 'flex', gap: 6, flexShrink: 0, alignItems: 'center' }}>
                                            <button
                                                onClick={() => { setWorkflowSubStepIdx(i => Math.max(0, i - 1)); setPage(1); }}
                                                disabled={workflowSubStepIdx === 0}
                                                title="Sub-paso anterior"
                                                style={{
                                                    display: 'flex', alignItems: 'center', gap: 4,
                                                    padding: '5px 10px', borderRadius: 8,
                                                    border: '1.5px solid #DDE3E6', backgroundColor: '#FFFFFF',
                                                    color: '#525256', fontSize: 12, fontWeight: 600,
                                                    cursor: workflowSubStepIdx === 0 ? 'not-allowed' : 'pointer',
                                                    opacity: workflowSubStepIdx === 0 ? 0.35 : 1,
                                                    transition: 'all 0.15s',
                                                }}
                                                onMouseEnter={e => { if (workflowSubStepIdx > 0) e.currentTarget.style.borderColor = '#9F9F9F'; }}
                                                onMouseLeave={e => { e.currentTarget.style.borderColor = '#DDE3E6'; }}
                                            >
                                                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6" /></svg>
                                                Anterior
                                            </button>
                                            <button
                                                onClick={() => {
                                                    if (isLast) {
                                                        // Finalizar: marcar último paso como completo y salir del flujo
                                                        const newSet = new Set([...completedPasos, step.paso]);
                                                        updateCompletedPasos(activeClasificacion, [...newSet]);
                                                        exitWorkflowMode(true); // <- activar filtros balanceado + validado
                                                    } else {
                                                        // Avanzar: marcar el paso actual como completo si terminamos sus 2 sub-pasos
                                                        if (isLastSubInPaso) {
                                                            const newSet = new Set([...completedPasos, step.paso]);
                                                            updateCompletedPasos(activeClasificacion, [...newSet]);
                                                        }
                                                        setWorkflowSubStepIdx(i => i + 1);
                                                        setPage(1);
                                                    }
                                                }}
                                                title={isLast ? 'Finalizar flujo de validación' : 'Avanzar al siguiente sub-paso'}
                                                style={{
                                                    display: 'flex', alignItems: 'center', gap: 4,
                                                    padding: '5px 10px', borderRadius: 8,
                                                    border: `1.5px solid ${isLast ? '#299D91' : allDone ? '#299D91' : '#DDE3E6'}`,
                                                    backgroundColor: isLast ? '#299D91' : allDone ? '#299D91' : '#FFFFFF',
                                                    color: isLast || allDone ? '#FFFFFF' : '#525256',
                                                    fontSize: 12, fontWeight: 600,
                                                    cursor: 'pointer',
                                                    transition: 'all 0.15s',
                                                }}
                                                onMouseEnter={e => { e.currentTarget.style.opacity = '0.85'; }}
                                                onMouseLeave={e => { e.currentTarget.style.opacity = '1'; }}
                                            >
                                                {isLast ? 'Finalizar' : allDone ? '¡Siguiente!' : 'Siguiente'}
                                                {isLast
                                                    ? <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
                                                    : <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6" /></svg>
                                                }
                                            </button>
                                        </div>
                                    </div>

                                    {/* Barra de progreso del sub-paso */}
                                    <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 10 }}>
                                        <div style={{ flex: 1, height: 5, borderRadius: 99, backgroundColor: '#E5E7EB', overflow: 'hidden' }}>
                                            <div style={{
                                                height: '100%', borderRadius: 99,
                                                width: `${pct}%`,
                                                backgroundColor: allDone ? '#299D91' : meta.color,
                                                transition: 'width 0.3s ease, background-color 0.2s',
                                            }} />
                                        </div>
                                        <span style={{ fontSize: 11, fontWeight: 700, color: allDone ? '#299D91' : meta.color, flexShrink: 0 }}>
                                            {revisados}/{total}
                                            {validados > 0 && <span style={{ color: '#299D91', marginLeft: 4 }}>✓{validados}</span>}
                                            {rechazados > 0 && <span style={{ color: '#D94A38', marginLeft: 4 }}>✗{rechazados}</span>}
                                        </span>
                                    </div>
                                </div>
                            );
                        })()}

                        {/* ── Toolbar ── */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: `8px ${PX}px`, ...borderBottom }}>
                            {/* Filtrar — dropdown unificado con secciones Estado y Variación */}
                            <div style={{ position: 'relative' }}>
                                <button
                                    onClick={() => setShowFilterMenu(v => !v)}
                                    style={{
                                        display: 'flex', alignItems: 'center', gap: 8, padding: '9px 16px',
                                        borderRadius: 12, fontSize: 13, fontWeight: 600, cursor: 'pointer',
                                        border: `1px solid ${filterRevision || (!workflowMode && (filterEstadoIdx || filterVariacion)) ? '#299D91' : '#E8E8E8'}`,
                                        color: filterRevision || (!workflowMode && (filterEstadoIdx || filterVariacion)) ? '#299D91' : '#525256',
                                        backgroundColor: filterRevision || (!workflowMode && (filterEstadoIdx || filterVariacion)) ? '#EBF7F6' : '#FAFAFA',
                                        transition: 'all 0.15s',
                                    }}
                                >
                                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
                                    </svg>
                                    {(() => {
                                        const parts = [];
                                        if (!workflowMode && filterEstadoIdx) parts.push(`Estado ${filterEstadoIdx}`);
                                        if (!workflowMode && filterVariacion) parts.push(`${filterVariacion} var.`);
                                        if (filterRevision) parts.push(filterRevision);
                                        return parts.length > 0 ? parts.join(' · ') : 'Filtrar';
                                    })()}
                                </button>

                                {showFilterMenu && (
                                    <div style={{ position: 'absolute', top: 'calc(100% + 8px)', left: 0, zIndex: 50, backgroundColor: '#FFFFFF', borderRadius: 14, border: '1px solid #DDE3E6', boxShadow: '0 12px 24px -4px rgba(0,0,0,0.12), 0 4px 8px -2px rgba(0,0,0,0.06)', padding: '16px 18px 14px', minWidth: workflowMode ? 220 : 460 }}>
                                        <div style={{ display: 'grid', gridTemplateColumns: workflowMode ? '1fr' : '1fr 1fr 1fr', gap: '0 24px' }}>

                                            {/* Columna Estado — bloqueada en modo guiado */}
                                            {!workflowMode && (
                                                <div>
                                                    <p style={{ margin: '0 0 8px', fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#9F9F9F' }}>Estado</p>
                                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                                        {[null, 1, 2, 3].map(val => {
                                                            const active = filterEstadoIdx === val;
                                                            const chipColors = { 1: { bg: '#EBF7F6', color: '#299D91', activeBg: '#299D91' }, 2: { bg: '#FFF7ED', color: '#D97706', activeBg: '#F0A050' }, 3: { bg: '#FFF0EE', color: '#D94A38', activeBg: '#D94A38' } };
                                                            const cc = val ? chipColors[val] : null;
                                                            return (
                                                                <button key={val ?? 'est-all'} onClick={() => { setFilterEstadoIdx(val); setPage(1); }}
                                                                    style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 10px', borderRadius: 8, fontSize: 12, fontWeight: active ? 700 : 500, cursor: 'pointer', border: `1px solid ${active && cc ? cc.activeBg : active ? '#299D91' : '#E8E8E8'}`, backgroundColor: active ? (cc ? cc.activeBg : '#299D91') : '#FAFAFA', color: active ? '#FFFFFF' : (cc ? cc.color : '#525256'), transition: 'all 0.12s', textAlign: 'left', width: '100%' }}
                                                                    onMouseEnter={e => { if (!active) { e.currentTarget.style.backgroundColor = cc ? cc.bg : '#F0F9FF'; e.currentTarget.style.borderColor = cc ? cc.activeBg : '#299D91'; } }}
                                                                    onMouseLeave={e => { if (!active) { e.currentTarget.style.backgroundColor = '#FAFAFA'; e.currentTarget.style.borderColor = '#E8E8E8'; } }}
                                                                >
                                                                    {val === null ? 'Todos' : `Estado ${val}`}
                                                                </button>
                                                            );
                                                        })}
                                                    </div>
                                                </div>
                                            )}

                                            {/* Columna Variación — bloqueada en modo guiado */}
                                            {!workflowMode && (
                                                <div>
                                                    <p style={{ margin: '0 0 8px', fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#9F9F9F' }}>Variación</p>
                                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                                        {[null, 'Baja', 'Alta'].map(val => {
                                                            const active = filterVariacion === val;
                                                            const varColors = { 'Baja': { bg: '#EBF7F6', color: '#299D91', activeBg: '#299D91' }, 'Alta': { bg: '#FFF0EE', color: '#D94A38', activeBg: '#D94A38' } };
                                                            const cc = val ? varColors[val] : null;
                                                            return (
                                                                <button key={val ?? 'var-all'} onClick={() => { setFilterVariacion(val); setPage(1); }}
                                                                    style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 10px', borderRadius: 8, fontSize: 12, fontWeight: active ? 700 : 500, cursor: 'pointer', border: `1px solid ${active && cc ? cc.activeBg : active ? '#299D91' : '#E8E8E8'}`, backgroundColor: active ? (cc ? cc.activeBg : '#299D91') : '#FAFAFA', color: active ? '#FFFFFF' : (cc ? cc.color : '#525256'), transition: 'all 0.12s', textAlign: 'left', width: '100%' }}
                                                                    onMouseEnter={e => { if (!active) { e.currentTarget.style.backgroundColor = cc ? cc.bg : '#F0F9FF'; e.currentTarget.style.borderColor = cc ? cc.activeBg : '#299D91'; } }}
                                                                    onMouseLeave={e => { if (!active) { e.currentTarget.style.backgroundColor = '#FAFAFA'; e.currentTarget.style.borderColor = '#E8E8E8'; } }}
                                                                >
                                                                    {val === null ? 'Todas' : val}
                                                                </button>
                                                            );
                                                        })}
                                                    </div>
                                                </div>
                                            )}

                                            {/* Columna Revisión — siempre disponible */}
                                            <div>
                                                <p style={{ margin: '0 0 8px', fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#9F9F9F' }}>Revisión</p>
                                                {workflowMode && (
                                                    <p style={{ margin: '0 0 8px', fontSize: 10, color: '#B0B0B0' }}>Estado y Variación son gestionados por el flujo guiado.</p>
                                                )}
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                                    {[null, 'Validado', 'Rechazado', 'Sin revisar'].map(val => {
                                                        const active = filterRevision === val;
                                                        const revColors = { 'Validado': { bg: '#EBF7F6', color: '#299D91', activeBg: '#299D91' }, 'Rechazado': { bg: '#FFF0EE', color: '#D94A38', activeBg: '#D94A38' }, 'Sin revisar': { bg: '#F3F4F6', color: '#71717A', activeBg: '#71717A' } };
                                                        const cc = val ? revColors[val] : null;
                                                        return (
                                                            <button key={val ?? 'rev-all'} onClick={() => { setFilterRevision(val); setPage(1); }}
                                                                style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 10px', borderRadius: 8, fontSize: 12, fontWeight: active ? 700 : 500, cursor: 'pointer', border: `1px solid ${active && cc ? cc.activeBg : active ? '#299D91' : '#E8E8E8'}`, backgroundColor: active ? (cc ? cc.activeBg : '#299D91') : '#FAFAFA', color: active ? '#FFFFFF' : (cc ? cc.color : '#525256'), transition: 'all 0.12s', textAlign: 'left', width: '100%' }}
                                                                onMouseEnter={e => { if (!active) { e.currentTarget.style.backgroundColor = cc ? cc.bg : '#F0F9FF'; e.currentTarget.style.borderColor = cc ? cc.activeBg : '#299D91'; } }}
                                                                onMouseLeave={e => { if (!active) { e.currentTarget.style.backgroundColor = '#FAFAFA'; e.currentTarget.style.borderColor = '#E8E8E8'; } }}
                                                            >
                                                                {val === null ? 'Todas' : val}
                                                            </button>
                                                        );
                                                    })}
                                                </div>
                                            </div>
                                        </div>
                                        {/* Footer: limpiar filtros */}
                                        {((!workflowMode && (filterEstadoIdx || filterVariacion)) || filterRevision) && (
                                            <div style={{ marginTop: 14, paddingTop: 12, borderTop: '1px solid #F0F0F0', display: 'flex', justifyContent: 'flex-end' }}>
                                                <button
                                                    onClick={() => { if (!workflowMode) { setFilterEstadoIdx(null); setFilterVariacion(null); } setFilterRevision(null); setShowFilterMenu(false); setPage(1); }}
                                                    style={{ padding: '6px 14px', borderRadius: 8, fontSize: 12, fontWeight: 600, color: '#D94A38', backgroundColor: 'transparent', border: '1px solid #D94A38', cursor: 'pointer', transition: 'all 0.12s' }}
                                                    onMouseEnter={e => { e.currentTarget.style.backgroundColor = '#FFF0EE'; }}
                                                    onMouseLeave={e => { e.currentTarget.style.backgroundColor = 'transparent'; }}
                                                >
                                                    Limpiar filtros
                                                </button>
                                            </div>
                                        )}
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

                            {/* Acciones — no encogen */}
                            <div style={{ display: 'flex', alignItems: 'center', gap: 0 }}>
                                <button
                                    onClick={handleValidar}
                                    disabled={selCount === 0}
                                    style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px', borderRadius: 8, fontSize: 12, fontWeight: 700, cursor: selCount === 0 ? 'default' : 'pointer', border: 'none', backgroundColor: '#299D91', color: '#FFFFFF', flexShrink: 0, transition: 'all 0.15s', opacity: selCount === 0 ? 0.45 : 1, minWidth: 0 }}
                                    onMouseEnter={e => { if (selCount > 0) e.currentTarget.style.backgroundColor = '#22857a'; }}
                                    onMouseLeave={e => e.currentTarget.style.backgroundColor = '#299D91'}
                                >
                                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                        <polyline points="20 6 9 17 4 12" />
                                    </svg>
                                    {selCount > 0 ? `Validar (${selCount})` : 'Validar'}
                                </button>
                                <button
                                    onClick={handleRechazar}
                                    disabled={selCount === 0}
                                    style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px', borderRadius: 8, fontSize: 12, fontWeight: 700, cursor: selCount === 0 ? 'default' : 'pointer', border: 'none', backgroundColor: '#D94A38', color: '#FFFFFF', flexShrink: 0, transition: 'all 0.15s', opacity: selCount === 0 ? 0.45 : 1, marginLeft: 6, minWidth: 0 }}
                                    onMouseEnter={e => { if (selCount > 0) e.currentTarget.style.backgroundColor = '#b83c2d'; }}
                                    onMouseLeave={e => e.currentTarget.style.backgroundColor = '#D94A38'}
                                >
                                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                        <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                                    </svg>
                                    {selCount > 0 ? `Rechazar (${selCount})` : 'Rechazar'}
                                </button>
                            </div>
                            <button
                                onClick={handleValidarTodosFiltrados}
                                disabled={filtered.filter(r => revisiones[r.ID] !== 'Validado').length === 0}
                                style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px', borderRadius: 8, fontSize: 12, fontWeight: 700, cursor: filtered.filter(r => revisiones[r.ID] !== 'Validado').length === 0 ? 'default' : 'pointer', border: 'none', backgroundColor: '#1e7c72', color: '#FFFFFF', flexShrink: 0, transition: 'all 0.15s', opacity: filtered.filter(r => revisiones[r.ID] !== 'Validado').length === 0 ? 0.45 : 1, marginLeft: 18, minWidth: 0 }}
                                title="Validar todos los instrumentos filtrados"
                                onMouseEnter={e => { if (filtered.filter(r => revisiones[r.ID] !== 'Validado').length > 0) e.currentTarget.style.backgroundColor = '#17635b'; }}
                                onMouseLeave={e => e.currentTarget.style.backgroundColor = '#1e7c72'}
                            >
                                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 2 }}>
                                    <polyline points="20 6 9 17 4 12" />
                                </svg>
                                Validar todos filtrados
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
                            <div style={{ width: COL.pct_antiguo, flexShrink: 0, textAlign: 'right', position: 'relative' }}>
                                <div style={{ display: 'inline-flex', alignItems: 'center', gap: 4, justifyContent: 'flex-end' }}>
                                    <span style={{ color: pctAntiguoFilter ? '#299D91' : undefined }}>PCT Antiguo</span>
                                    <button
                                        onMouseDown={e => { e.stopPropagation(); setShowPctAntiguoMenu(v => !v); setShowPctNuevoMenu(false); }}
                                        title="Filtrar por clasificación antigua"
                                        style={{ width: 20, height: 20, borderRadius: 5, border: 'none', background: pctAntiguoFilter ? '#EBF7F6' : 'transparent', cursor: 'pointer', color: pctAntiguoFilter ? '#299D91' : '#9F9F9F', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', transition: 'all 0.15s', flexShrink: 0 }}
                                    >
                                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9" /></svg>
                                    </button>
                                </div>
                                {showPctAntiguoMenu && (
                                    <div onMouseDown={e => e.stopPropagation()} style={{ position: 'absolute', right: 0, top: 'calc(100% + 8px)', zIndex: 60, backgroundColor: '#FFFFFF', borderRadius: 10, border: '1px solid #DDE3E6', boxShadow: '0 12px 24px rgba(0,0,0,0.10)', padding: '6px 4px', minWidth: 150, maxHeight: 260, overflowY: 'auto' }}>
                                        {[null, ...uniqueAntiguas].map(v => (
                                            <button key={v ?? '__all__'} onClick={() => { setPctAntiguoFilter(v); setShowPctAntiguoMenu(false); setPage(1); }}
                                                style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%', textAlign: 'left', padding: '7px 12px', border: 'none', borderRadius: 6, background: (v === null ? pctAntiguoFilter == null : pctAntiguoFilter === v) ? '#EBF7F6' : 'transparent', cursor: 'pointer', fontSize: 13, fontWeight: (v === null ? pctAntiguoFilter == null : pctAntiguoFilter === v) ? 700 : 400, color: (v === null ? pctAntiguoFilter == null : pctAntiguoFilter === v) ? '#299D91' : '#191919' }}
                                            >{v ?? 'Todos'}</button>
                                        ))}
                                    </div>
                                )}
                            </div>

                            <div style={{ width: COL.pct_nuevo, flexShrink: 0, textAlign: 'right', position: 'relative' }}>
                                <div style={{ display: 'inline-flex', alignItems: 'center', gap: 4, justifyContent: 'flex-end' }}>
                                    <span style={{ color: pctNuevoFilter ? '#299D91' : undefined }}>PCT Nuevo</span>
                                    <button
                                        onMouseDown={e => { e.stopPropagation(); setShowPctNuevoMenu(v => !v); setShowPctAntiguoMenu(false); }}
                                        title="Filtrar por clasificación nueva"
                                        style={{ width: 20, height: 20, borderRadius: 5, border: 'none', background: pctNuevoFilter ? '#EBF7F6' : 'transparent', cursor: 'pointer', color: pctNuevoFilter ? '#299D91' : '#9F9F9F', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', transition: 'all 0.15s', flexShrink: 0 }}
                                    >
                                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9" /></svg>
                                    </button>
                                </div>
                                {showPctNuevoMenu && (
                                    <div onMouseDown={e => e.stopPropagation()} style={{ position: 'absolute', right: 0, top: 'calc(100% + 8px)', zIndex: 60, backgroundColor: '#FFFFFF', borderRadius: 10, border: '1px solid #DDE3E6', boxShadow: '0 12px 24px rgba(0,0,0,0.10)', padding: '6px 4px', minWidth: 150, maxHeight: 260, overflowY: 'auto' }}>
                                        {[null, ...uniqueNuevas].map(v => (
                                            <button key={v ?? '__all__'} onClick={() => { setPctNuevoFilter(v); setShowPctNuevoMenu(false); setPage(1); }}
                                                style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%', textAlign: 'left', padding: '7px 12px', border: 'none', borderRadius: 6, background: (v === null ? pctNuevoFilter == null : pctNuevoFilter === v) ? '#EBF7F6' : 'transparent', cursor: 'pointer', fontSize: 13, fontWeight: (v === null ? pctNuevoFilter == null : pctNuevoFilter === v) ? 700 : 400, color: (v === null ? pctNuevoFilter == null : pctNuevoFilter === v) ? '#299D91' : '#191919' }}
                                            >{v ?? 'Todos'}</button>
                                        ))}
                                    </div>
                                )}
                            </div>

                            <div style={{ width: COL.variacion, flexShrink: 0, textAlign: 'right' }}>
                                <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, justifyContent: 'flex-end' }}>
                                    <span>Variación</span>
                                    <button
                                        onClick={() => setVariacionSort(s => s === null ? 'desc' : s === 'desc' ? 'asc' : null)}
                                        title={variacionSort === null ? 'Ordenar mayor → menor' : variacionSort === 'desc' ? 'Ordenar menor → mayor' : 'Quitar orden'}
                                        style={{ width: 20, height: 20, borderRadius: 5, border: 'none', background: variacionSort ? '#EBF7F6' : 'transparent', cursor: 'pointer', color: variacionSort ? '#299D91' : '#9F9F9F', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', transition: 'all 0.15s' }}
                                    >
                                        {variacionSort === 'asc' ? (
                                            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="18 15 12 9 6 15" /></svg>
                                        ) : variacionSort === 'desc' ? (
                                            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9" /></svg>
                                        ) : (
                                            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="8" y1="6" x2="16" y2="6" /><line x1="6" y1="12" x2="18" y2="12" /><line x1="8" y1="18" x2="16" y2="18" /></svg>
                                        )}
                                    </button>
                                </div>
                            </div>
                            <div style={{ width: COL.acciones, flexShrink: 0 }} />
                        </div>

                        {/* ── Filas ── */}
                        <div key={filterKey} style={{ animation: 'fadeIn 0.2s ease both' }}>
                            {paged.length === 0 ? (
                                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12, padding: '64px 0', color: '#9F9F9F' }}>
                                    <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                        <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
                                    </svg>
                                    <p style={{ fontSize: 14, fontWeight: 500 }}>Sin resultados para la búsqueda</p>
                                </div>
                            ) : paged.map((row, idx) => {
                                const isSel = selected.includes(row.ID);
                                const revision = revisiones[row.ID] || null;
                                const isValidado = revision === 'Validado';
                                const isRechazado = revision === 'Rechazado';
                                const hoverBg = isValidado ? '#D4F4F0' : isRechazado ? '#FFE4E0' : '#E2E8F0';
                                const restBg = isValidado ? '#E9F9F7' : isRechazado ? '#FFF0EE' : isSel ? '#F0FFFE' : 'transparent';
                                return (
                                    <div
                                        key={row.ID}
                                        style={{ ...rowStyle(isSel, revision), ...(idx < paged.length - 1 ? { borderBottom: `1px solid ${isValidado ? '#C5EDE9' : isRechazado ? '#FFD8D3' : '#F5F5F5'}` } : {}) }}
                                        onMouseEnter={e => { e.currentTarget.style.backgroundColor = hoverBg; }}
                                        onMouseLeave={e => { e.currentTarget.style.backgroundColor = restBg; }}
                                        onClick={() => { onSelect(row.ID); onNavigate('visualizacion'); }}
                                    >
                                        {/* Checkbox */}
                                        <div style={{ width: COL.check, flexShrink: 0, marginRight: 12 }} onClick={(e) => { e.stopPropagation(); toggleRow(row.ID); }}>
                                            <input type="checkbox" readOnly checked={isSel || isValidado} style={{ width: 15, height: 15, cursor: 'pointer', accentColor: isRechazado ? '#D94A38' : '#299D91' }} />
                                        </div>

                                        {/* Expand */}
                                        <div style={{ width: COL.expand, flexShrink: 0, marginRight: 16, color: '#CCCCCC' }}>
                                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                                <circle cx="12" cy="12" r="10" />
                                                <line x1="12" y1="8" x2="12" y2="16" /><line x1="8" y1="12" x2="16" y2="12" />
                                            </svg>
                                        </div>

                                        {/* Instrumento */}
                                        <div style={{ flex: 1, minWidth: 0, paddingRight: 16, display: 'flex', alignItems: 'center', gap: 6 }}>
                                            {row.alerta_dominancia && <AlertaDominanciaIcon tipo={row.alerta_dominancia} />}
                                            <p style={{ margin: 0, fontSize: 15, fontWeight: 600, color: '#191919', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: '1 1 0', minWidth: 0 }}>
                                                {row.Nombre}
                                            </p>
                                            <button
                                                onClick={e => { e.stopPropagation(); window.open(`https://web.finantech.cl/admin/instruments/${row.ID}`, '_blank'); }}
                                                title="Ver en Finantech"
                                                style={{
                                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                    width: 24, height: 24, borderRadius: 6, border: 'none',
                                                    backgroundColor: 'transparent', color: '#9F9F9F', cursor: 'pointer',
                                                    flexShrink: 0, padding: 0,
                                                }}
                                                onMouseEnter={e => { e.currentTarget.style.backgroundColor = '#EBF7F6'; e.currentTarget.style.color = '#299D91'; }}
                                                onMouseLeave={e => { e.currentTarget.style.backgroundColor = 'transparent'; e.currentTarget.style.color = '#9F9F9F'; }}
                                            >
                                                <ExternalLinkIcon />
                                            </button>
                                        </div>

                                        {/* ID */}
                                        <div style={{ width: COL.id_inst, flexShrink: 0, fontSize: 14, color: '#525256' }}>{row.ID}</div>

                                        {/* Estado - Formateado y coloreado */}
                                        {(() => {
                                            // Mapea Estado_1, Estado_2, Estado_3 a texto y color
                                            const estadoMap = {
                                                'Estado_1': { label: 'Estado 1', color: '#299D91' }, // verde
                                                'Estado_2': { label: 'Estado 2', color: '#F0A050' }, // amarillo
                                                'Estado_3': { label: 'Estado 3', color: '#D94A38' }  // rojo
                                            };
                                            const estado = estadoMap[row.Estado];
                                            return (
                                                <div style={{ width: COL.estado, flexShrink: 0, fontSize: 14, fontWeight: 700, color: estado ? estado.color : '#525256' }}>
                                                    {estado ? estado.label : (row.Estado || '')}
                                                </div>
                                            );
                                        })()}

                                        {/* PCT Antiguo */}
                                        <div style={{ width: COL.pct_antiguo, flexShrink: 0, textAlign: 'right' }}>
                                            <span style={{ fontSize: 14, fontWeight: 600, color: '#191919' }}>
                                                {row.pct_dominancia_antigua != null ? formatPctDominancia(row.pct_dominancia_antigua) : '-'}
                                            </span>
                                        </div>

                                        {/* PCT Nuevo */}
                                        <div style={{ width: COL.pct_nuevo, flexShrink: 0, textAlign: 'right' }}>
                                            <span style={{ fontSize: 14, fontWeight: 600, color: '#191919' }}>
                                                {(row.pct_dominancia_nuevo ?? row.pct_dominancia_nueva) != null ? formatPctDominancia(row.pct_dominancia_nuevo ?? row.pct_dominancia_nueva) : '-'}
                                            </span>
                                        </div>

                                        {/* Variación */}
                                        {(() => {
                                            const variacion = row.variacion_balanceados != null
                                                ? row.variacion_balanceados
                                                : row.variacion_no_balanceados;
                                            return (
                                                <div style={{ width: COL.variacion, flexShrink: 0, textAlign: 'right' }}>
                                                    <span style={{ fontSize: 14, fontWeight: 600, color: '#191919' }}>
                                                        {formatVariacion(variacion)}
                                                    </span>
                                                </div>
                                            );
                                        })()}

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
                        </div>

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
                            {/* Mostrar contador de filtros si hay filtros aplicados */}
                            {filtered.length < SAMPLE_DATA.length && (
                                <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#525256', fontWeight: 500 }}>
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#299D91" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
                                    </svg>
                                    <span>
                                        Filtros aplicados: <strong style={{ color: '#299D91' }}>{filtered.length}</strong> de {SAMPLE_DATA.length} instrumentos
                                    </span>
                                </div>
                            )}
                            <button
                                onClick={() => handleDownload('balanceados')}
                                disabled={downloading === 'balanceados'}
                                style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 18px', borderRadius: 10, fontSize: 13, fontWeight: 700, cursor: downloading === 'balanceados' ? 'default' : 'pointer', border: 'none', backgroundColor: downloading === 'balanceados' ? '#cccccc' : '#299D91', color: '#FFFFFF', transition: 'all 0.15s', opacity: downloading === 'balanceados' ? 0.6 : 1 }}
                                onMouseEnter={e => { if (downloading !== 'balanceados') e.currentTarget.style.backgroundColor = '#22857a'; }}
                                onMouseLeave={e => { if (downloading !== 'balanceados') e.currentTarget.style.backgroundColor = '#299D91'; }}
                            >
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" />
                                </svg>
                                {downloading === 'balanceados' ? 'Descargando...' : 'Generar Balanceado'}
                            </button>
                            <button
                                onClick={() => handleDownload('no_balanceados')}
                                disabled={downloading === 'no_balanceados'}
                                style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 18px', borderRadius: 10, fontSize: 13, fontWeight: 700, cursor: downloading === 'no_balanceados' ? 'default' : 'pointer', border: 'none', backgroundColor: downloading === 'no_balanceados' ? '#cccccc' : '#F0A050', color: '#FFFFFF', transition: 'all 0.15s', opacity: downloading === 'no_balanceados' ? 0.6 : 1 }}
                                onMouseEnter={e => { if (downloading !== 'no_balanceados') e.currentTarget.style.backgroundColor = '#d98a3d'; }}
                                onMouseLeave={e => { if (downloading !== 'no_balanceados') e.currentTarget.style.backgroundColor = '#F0A050'; }}
                            >
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" />
                                </svg>
                                {downloading === 'no_balanceados' ? 'Descargando...' : 'Generar no balanceados'}
                            </button>
                            <button
                                onClick={() => handleDownload('sin_datos')}
                                disabled={downloading === 'sin_datos'}
                                style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 18px', borderRadius: 10, fontSize: 13, fontWeight: 700, cursor: downloading === 'sin_datos' ? 'default' : 'pointer', border: 'none', backgroundColor: downloading === 'sin_datos' ? '#cccccc' : '#9F9F9F', color: '#FFFFFF', transition: 'all 0.15s', opacity: downloading === 'sin_datos' ? 0.6 : 1 }}
                                onMouseEnter={e => { if (downloading !== 'sin_datos') e.currentTarget.style.backgroundColor = '#8a8a8a'; }}
                                onMouseLeave={e => { if (downloading !== 'sin_datos') e.currentTarget.style.backgroundColor = '#9F9F9F'; }}
                            >
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" />
                                </svg>
                                {downloading === 'sin_datos' ? 'Descargando...' : 'Generar sin datos'}
                            </button>
                        </div>

                    </div>{/* fin card */}

                </>
            )}{/* fin contenido principal */}

        </div>
    );
}

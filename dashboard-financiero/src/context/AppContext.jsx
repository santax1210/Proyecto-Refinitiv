import { createContext, useContext, useState, useCallback } from 'react';
import * as api from '../services/apiService';

// Normaliza el valor de clasificación al key interno usado para almacenamiento
// Debe coincidir con la lógica del backend (normalize_clasificacion)
export function normalizeClasifKey(c) {
    const v = String(c || 'moneda').toLowerCase().trim();
    if (v.includes('regi')) return 'region';
    if (v.includes('indus') || v.includes('sector')) return 'sector';
    return 'moneda';
}

const EMPTY_MAP = { moneda: null, region: null, sector: null };

/**
 * Contexto global de la aplicación para manejar:
 * - Estado de archivos subidos
 * - Estado del procesamiento
 * - Datos procesados
 */

const AppContext = createContext(null);


export function AppProvider({ children }) {
    const [uploadedFiles, setUploadedFiles] = useState([]);
    const [processingState, setProcessingState] = useState({
        status: 'idle', // idle, uploading, processing, completed, error
        progress: 0,
        message: '',
        error: null,
    });
    // Estado de datos por clasificación (moneda / region / sector)
    const [validationDataMap, setValidationDataMap] = useState({ ...EMPTY_MAP });
    const [summaryMap, setSummaryMap] = useState({ ...EMPTY_MAP });
    const [clasificacion, setClasificacion] = useState('');
    // Clasificación actualmente visualizada en ValidacionPage
    const [activeClasificacion, _setActiveClasificacion] = useState(() => {
        try { return localStorage.getItem('allocations_active_clasif') || ''; } catch { return ''; }
    });

    // Pasos del flujo de validación completados (por clasificación)
    // Persiste en memoria durante la sesión — no se pierde al navegar
    const [completedPasosMap, setCompletedPasosMap] = useState(() => {
        try {
            const saved = localStorage.getItem('allocations_completed_pasos_map');
            return saved ? JSON.parse(saved) : { moneda: [], region: [], sector: [] };
        } catch { return { moneda: [], region: [], sector: [] }; }
    });

    const updateCompletedPasos = useCallback((clasifKey, pasosArray) => {
        setCompletedPasosMap(prev => {
            const next = { ...prev, [clasifKey]: pasosArray };
            try { localStorage.setItem('allocations_completed_pasos_map', JSON.stringify(next)); } catch { /* ignorar */ }
            return next;
        });
    }, []);

    const setActiveClasificacion = useCallback((key) => {
        _setActiveClasificacion(key);
        try { localStorage.setItem('allocations_active_clasif', key); } catch { /* ignorar */ }
    }, []);

    // Valores computados para la clasificación activa
    const validationData = validationDataMap[activeClasificacion] ?? null;
    const summary = summaryMap[activeClasificacion] ?? null;

    /**
     * Subir archivos y ejecutar pipeline completo
     */
    const uploadAndProcess = useCallback(async (files) => {
        try {
            // Usar la clasificacion global del contexto si existe, si no, fallback a la que venga en files o 'moneda'
            const clasif = clasificacion || files.clasificacion || 'moneda';
            const { clasificacion: _omit, ...fileMap } = files;

            const clasifKey = normalizeClasifKey(clasif);

            // Limpiar solo los datos de ESTA clasificación
            try { localStorage.removeItem(`allocations_revisiones_${clasifKey}`); } catch { /* ignorar */ }
            try { localStorage.removeItem(`allocations_filtros_${clasifKey}`); } catch { /* ignorar */ }
            try { localStorage.removeItem(`allocations_selected_${clasifKey}`); } catch { /* ignorar */ }
            try { localStorage.removeItem(`allocations_wf_mode_${clasifKey}`); } catch { /* ignorar */ }
            try { localStorage.removeItem(`allocations_wf_step_${clasifKey}`); } catch { /* ignorar */ }

            // Limpiar el progreso del flujo de validación para esta clasificación
            setCompletedPasosMap(prev => {
                const next = { ...prev, [clasifKey]: [] };
                try { localStorage.setItem('allocations_completed_pasos_map', JSON.stringify(next)); } catch { /* ignorar */ }
                return next;
            });

            // Actualizar estado a uploading
            setProcessingState({
                status: 'uploading',
                progress: 0,
                message: 'Subiendo archivos...',
                error: null,
            });

            // Subir archivos
            const uploadResult = await api.uploadFiles(fileMap, clasif);

            if (uploadResult.status === 'error') {
                throw new Error(uploadResult.message);
            }

            setUploadedFiles(uploadResult.files || []);

            // Iniciar procesamiento
            setProcessingState({
                status: 'processing',
                progress: 0,
                message: 'Iniciando procesamiento...',
                error: null,
            });

            await api.startProcessing(clasif);

            // Hacer polling del estado
            await api.pollProcessingStatus((status) => {
                setProcessingState({
                    status: 'processing',
                    progress: status.progress || 0,
                    message: status.message || 'Procesando...',
                    error: null,
                });
            });

            // Cargar resultados y guardar bajo la clasificación correcta
            const results = await api.getValidationResults(clasifKey);
            setValidationDataMap(prev => ({ ...prev, [clasifKey]: results.data }));
            setSummaryMap(prev => ({ ...prev, [clasifKey]: results.summary }));
            setActiveClasificacion(clasifKey);

            // Completado
            setProcessingState({
                status: 'completed',
                progress: 100,
                message: 'Procesamiento completado exitosamente',
                error: null,
            });

            return results;

        } catch (error) {
            console.error('Error en uploadAndProcess:', error);
            const errorMessage = error.message || 'Error desconocido en el procesamiento';
            setProcessingState({
                status: 'error',
                progress: 0,
                message: errorMessage,
                error: errorMessage,
            });
            throw error;
        }
    }, [clasificacion]);

    /**
     * Cargar resultados de validación para una clasificación específica (o la última procesada).
     * @param {string|null} clasifKey - 'moneda', 'region', 'sector'. null = usa la última procesada por el backend.
     */
    const loadValidationResults = useCallback(async (clasifKey) => {
        try {
            const results = await api.getValidationResults(clasifKey || null);
            // Guardamos bajo la clasificación que viene en el summary del backend
            const storeKey = results.summary?.clasificacion || clasifKey || 'moneda';
            setValidationDataMap(prev => ({ ...prev, [storeKey]: results.data }));
            setSummaryMap(prev => ({ ...prev, [storeKey]: results.summary }));
            // Si aún no hay clasificación activa, establecer la que se acaba de cargar
            _setActiveClasificacion(prev => {
                if (!prev) {
                    try { localStorage.setItem('allocations_active_clasif', storeKey); } catch { /* ignorar */ }
                    return storeKey;
                }
                return prev;
            });
            return results;
        } catch (error) {
            console.error('Error al cargar resultados:', error);
            throw error;
        }
    }, []);

    /**
     * Reiniciar estado
     */
    const resetProcessing = useCallback(async () => {
        try {
            await api.resetProcessing();
            setUploadedFiles([]);
            setProcessingState({
                status: 'idle',
                progress: 0,
                message: '',
                error: null,
            });
            setValidationDataMap({ ...EMPTY_MAP });
            setSummaryMap({ ...EMPTY_MAP });
            _setActiveClasificacion('');
            try { localStorage.removeItem('allocations_active_clasif'); } catch { /* ignorar */ }
        } catch (error) {
            console.error('Error al reiniciar:', error);
            throw error;
        }
    }, []);

    /**
     * Verificar salud de la API
     */
    const checkApiHealth = useCallback(async () => {
        try {
            return await api.checkHealth();
        } catch (error) {
            console.error('Error en health check:', error);
            return { status: 'error', message: error.message };
        }
    }, []);

    const value = {
        // Estado
        uploadedFiles,
        processingState,
        // Datos por clasificación
        validationDataMap,          // { moneda, region, sector } — para el selector de clasificación
        validationData,             // acceso directo a la clasificación activa
        summary,                    // acceso directo a la clasificación activa
        activeClasificacion,
        setActiveClasificacion,
        clasificacion,
        setClasificacion,
        // Progreso del flujo de validación
        completedPasosMap,
        updateCompletedPasos,
        // Acciones
        uploadAndProcess,
        loadValidationResults,
        resetProcessing,
        checkApiHealth,
        // Setters directos (para casos especiales)
        setUploadedFiles,
        setProcessingState,
    };

    return (
        <AppContext.Provider value={value}>
            {children}
        </AppContext.Provider>
    );
}

/**
 * Hook para usar el contexto de la aplicación
 */
export function useApp() {
    const context = useContext(AppContext);
    if (!context) {
        throw new Error('useApp debe ser usado dentro de AppProvider');
    }
    return context;
}

export default AppContext;

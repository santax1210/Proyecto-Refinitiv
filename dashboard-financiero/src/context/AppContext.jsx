import { createContext, useContext, useState, useCallback } from 'react';
import * as api from '../services/apiService';

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
    const [validationData, setValidationData] = useState(null);
    const [summary, setSummary] = useState(null);
    const [clasificacion, setClasificacion] = useState('');

    /**
     * Subir archivos y ejecutar pipeline completo
     */
    const uploadAndProcess = useCallback(async (files) => {
        try {
            // Usar la clasificacion global del contexto si existe, si no, fallback a la que venga en files o 'moneda'
            const clasif = clasificacion || files.clasificacion || 'moneda';
            const { clasificacion: _omit, ...fileMap } = files;

            // Limpiar revisiones guardadas del procesamiento anterior
            try { localStorage.removeItem('allocations_revisiones'); } catch { /* ignorar */ }

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

            // Cargar resultados
            const results = await api.getValidationResults();
            setValidationData(results.data);
            setSummary(results.summary);

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
     * Cargar resultados de validación (si ya fueron procesados)
     */
    const loadValidationResults = useCallback(async () => {
        try {
            const results = await api.getValidationResults();
            setValidationData(results.data);
            setSummary(results.summary);
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
            setValidationData(null);
            setSummary(null);
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
        validationData,
        summary,
        clasificacion,
        setClasificacion,
        // Acciones
        uploadAndProcess,
        loadValidationResults,
        resetProcessing,
        checkApiHealth,
        // Setters directos (para casos especiales)
        setUploadedFiles,
        setProcessingState,
        setValidationData,
        setSummary,
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

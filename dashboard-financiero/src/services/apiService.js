/**
 * Servicio de API para conectar con el backend Flask.
 * 
 * Base URL: http://localhost:5000
 */

const API_BASE_URL = 'http://localhost:5000';

/**
 * Helper para manejar respuestas de la API
 */
async function handleResponse(response) {
    const data = await response.json();
    
    if (!response.ok) {
        const errorMsg = data.message || `Error HTTP ${response.status}: ${response.statusText}`;
        throw new Error(errorMsg);
    }
    
    return data;
}

/**
 * Health check - Verificar que la API está funcionando
 */
export async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/health`);
        return await handleResponse(response);
    } catch (error) {
        console.error('Error en health check:', error);
        throw error;
    }
}

/**
 * Subir archivos CSV al backend
 * 
 * @param {Object} files - Objeto con los archivos a subir
 * @param {string} clasificacion - Tipo de clasificación ('Moneda', 'Región', 'Industria')
 */
export async function uploadFiles(files, clasificacion = 'moneda') {
    try {
        const formData = new FormData();
        
        // Agregar archivos al FormData con los nombres esperados por el backend
        if (files.posiciones) formData.append('posiciones', files.posiciones);
        if (files.instruments) formData.append('instruments', files.instruments);
        if (files.allocations_nuevas) formData.append('allocations_nuevas', files.allocations_nuevas);
        if (files.allocations_antiguas) formData.append('allocations_antiguas', files.allocations_antiguas);
        formData.append('clasificacion', clasificacion);
        
        console.log('Subiendo archivos:', Object.keys(files));
        
        const response = await fetch(`${API_BASE_URL}/api/upload`, {
            method: 'POST',
            body: formData,
        });
        
        return await handleResponse(response);
    } catch (error) {
        console.error('Error al subir archivos:', error);
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            throw new Error('No se puede conectar con el backend. ¿Está corriendo el servidor Flask en http://localhost:5000?');
        }
        throw error;
    }
}

/**
 * Iniciar el procesamiento del pipeline
 * @param {string} clasificacion - Tipo de clasificación
 */
export async function startProcessing(clasificacion = 'moneda') {
    try {
        console.log('Iniciando procesamiento del pipeline:', clasificacion);
        const response = await fetch(`${API_BASE_URL}/api/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ clasificacion }),
        });
        
        return await handleResponse(response);
    } catch (error) {
        console.error('Error al iniciar procesamiento:', error);
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            throw new Error('No se puede conectar con el backend para iniciar el procesamiento');
        }
        throw error;
    }
}

/**
 * Obtener el estado actual del procesamiento
 */
export async function getProcessingStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/status`);
        return await handleResponse(response);
    } catch (error) {
        console.error('Error al obtener estado:', error);
        throw error;
    }
}

/**
 * Polling del estado del procesamiento hasta que se complete
 * 
 * @param {Function} onProgress - Callback para actualizar progreso (recibe el estado)
 * @param {Number} interval - Intervalo de polling en ms (default: 2000)
 */
export async function pollProcessingStatus(onProgress, interval = 2000) {
    return new Promise((resolve, reject) => {
        const pollInterval = setInterval(async () => {
            try {
                const status = await getProcessingStatus();
                
                // Llamar callback con el estado actualizado
                if (onProgress) {
                    onProgress(status);
                }
                
                // Si completó o hubo error, detener polling
                if (status.status === 'completed') {
                    clearInterval(pollInterval);
                    resolve(status);
                } else if (status.status === 'error') {
                    clearInterval(pollInterval);
                    reject(new Error(status.error || 'Error en el procesamiento'));
                }
            } catch (error) {
                clearInterval(pollInterval);
                reject(error);
            }
        }, interval);
    });
}

/**
 * Obtener resultados de validación para la tabla
 */
export async function getValidationResults() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/results/validation`);
        return await handleResponse(response);
    } catch (error) {
        console.error('Error al obtener resultados de validación:', error);
        throw error;
    }
}

/**
 * Obtener datos de un export específico
 * 
 * @param {String} exportType - Tipo de export: 'balanceados', 'no_balanceados', 'con_cambios', 'sin_datos'
 */
export async function getExportData(exportType) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/results/exports/${exportType}`);
        return await handleResponse(response);
    } catch (error) {
        console.error(`Error al obtener export ${exportType}:`, error);
        throw error;
    }
}

/**
 * Descargar un archivo CSV de export
 * 
 * @param {String} exportType - Tipo de export: 'balanceados', 'no_balanceados', 'con_cambios', 'sin_datos'
 */
export async function downloadExport(exportType) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/download/${exportType}`);
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.message || 'Error al descargar archivo');
        }
        
        // Descargar el archivo
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `export_${exportType}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        return { status: 'success', message: 'Archivo descargado' };
    } catch (error) {
        console.error(`Error al descargar export ${exportType}:`, error);
        throw error;
    }
}

/**
 * Descargar un archivo CSV de export filtrado por IDs
 * 
 * @param {String} exportType - Tipo de export: 'balanceados', 'no_balanceados', 'con_cambios', 'sin_datos'
 * @param {Array} instrumentIds - Array de IDs de instrumentos a incluir en el export
 */
export async function downloadFilteredExport(exportType, instrumentIds) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/download-filtered/${exportType}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                instrument_ids: instrumentIds
            })
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.message || 'Error al descargar archivo filtrado');
        }
        
        // Descargar el archivo
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `export_${exportType}_filtrado.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        return { status: 'success', message: 'Archivo filtrado descargado' };
    } catch (error) {
        console.error(`Error al descargar export filtrado ${exportType}:`, error);
        throw error;
    }
}

/**
 * Reiniciar el estado del procesamiento
 */
export async function resetProcessing() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/reset`, {
            method: 'DELETE',
        });
        
        return await handleResponse(response);
    } catch (error) {
        console.error('Error al reiniciar estado:', error);
        throw error;
    }
}

/**
 * Flujo completo: subir archivos y procesar
 * 
 * @param {Object} files - Archivos a subir
 * @param {Function} onProgress - Callback para progreso
 */
export async function uploadAndProcess(files, onProgress) {
    try {
        // 1. Subir archivos
        if (onProgress) onProgress({ stage: 'upload', progress: 0, message: 'Subiendo archivos...' });
        const uploadResult = await uploadFiles(files);
        
        if (uploadResult.status === 'error') {
            throw new Error(uploadResult.message);
        }
        
        // 2. Iniciar procesamiento
        if (onProgress) onProgress({ stage: 'process', progress: 0, message: 'Iniciando procesamiento...' });
        const processResult = await startProcessing();
        
        // 3. Hacer polling hasta que termine
        const finalStatus = await pollProcessingStatus((status) => {
            if (onProgress) {
                onProgress({
                    stage: 'processing',
                    progress: status.progress,
                    message: status.message,
                    status: status.status
                });
            }
        });
        
        return finalStatus;
    } catch (error) {
        console.error('Error en flujo completo:', error);
        throw error;
    }
}

export default {
    checkHealth,
    uploadFiles,
    startProcessing,
    getProcessingStatus,
    pollProcessingStatus,
    getValidationResults,
    getExportData,
    downloadExport,
    downloadFilteredExport,
    resetProcessing,
    uploadAndProcess,
};

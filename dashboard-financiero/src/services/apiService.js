/**
 * Servicio de API para conectar con el backend Flask.
 *
 * Base URL: /api (relativo, para producción con Nginx)
 *
 * Autenticación: JWT via localStorage.
 * - El token se guarda en localStorage bajo la clave 'auth_token'.
 * - Cada petición (excepto /api/login) incluye el header Authorization: Bearer <token>.
 * - Si el servidor responde 401, se limpia la sesión y se recarga la app.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

// ==================== AUTH HELPERS ====================

export function getToken() {
    return localStorage.getItem('auth_token');
}

export function saveToken(token) {
    localStorage.setItem('auth_token', token);
}

export function clearToken() {
    localStorage.removeItem('auth_token');
}

export function isAuthenticated() {
    return !!getToken();
}

/**
 * Login: envía credenciales y guarda el token si son correctas.
 * @returns {Promise<{status: string, token: string}>}
 */
export async function login(username, password) {
    const response = await fetch(`${API_BASE_URL}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.message || 'Error al iniciar sesión');
    }
    saveToken(data.token);
    return data;
}

export function logout() {
    clearToken();
}

// ==================== INTERNOS ====================

/**
 * Construye los headers base incluyendo el Authorization si hay token disponible.
 */
function authHeaders(extra = {}) {
    const token = getToken();
    const headers = { ...extra };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
}

/**
 * Helper para manejar respuestas de la API.
 * Si el servidor responde 401, limpia el token y fuerza recarga para volver al login.
 */
async function handleResponse(response) {
    if (response.status === 401) {
        clearToken();
        window.location.reload();
        throw new Error('Sesión expirada. Por favor, inicia sesión nuevamente.');
    }

    const data = await response.json();

    if (!response.ok) {
        const errorMsg = data.message || `Error HTTP ${response.status}: ${response.statusText}`;
        throw new Error(errorMsg);
    }

    return data;
}

// ==================== ENDPOINTS ====================

/**
 * Health check - Verificar que la API está funcionando (no requiere token)
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

        if (files.posiciones) formData.append('posiciones', files.posiciones);
        if (files.instruments) formData.append('instruments', files.instruments);
        if (files.allocations_nuevas) formData.append('allocations_nuevas', files.allocations_nuevas);
        if (files.allocations_antiguas) formData.append('allocations_antiguas', files.allocations_antiguas);
        formData.append('clasificacion', clasificacion);

        console.log('Subiendo archivos:', Object.keys(files));

        const response = await fetch(`${API_BASE_URL}/api/upload`, {
            method: 'POST',
            headers: authHeaders(),   // SIN Content-Type: browser lo pone solo para multipart
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
            headers: authHeaders({ 'Content-Type': 'application/json' }),
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
        const response = await fetch(`${API_BASE_URL}/api/status`, {
            headers: authHeaders(),
        });
        return await handleResponse(response);
    } catch (error) {
        console.error('Error al obtener estado:', error);
        throw error;
    }
}

/**
 * Obtener lista de clasificaciones que tienen resultados en disco
 */
export async function getAvailableResults() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/results/available`, {
            headers: authHeaders(),
        });
        return await handleResponse(response);
    } catch (error) {
        console.error('Error al obtener clasificaciones disponibles:', error);
        throw error;
    }
}

/**
 * Polling del estado del procesamiento hasta que se complete
 *
 * @param {Function} onProgress - Callback para actualizar progreso (recibe el estado)
 * @param {Number} interval - Intervalo de polling en ms (default: 2000)
 */
export async function pollProcessingStatus(onProgress, interval = 2000, timeoutMs = 300000) {
    return new Promise((resolve, reject) => {
        const startTime = Date.now();
        let lastProcessingTime = Date.now();

        const pollInterval = setInterval(async () => {
            try {
                const status = await getProcessingStatus();

                if (onProgress) {
                    onProgress(status);
                }

                if (status.status === 'completed') {
                    clearInterval(pollInterval);
                    resolve(status);
                    return;
                } else if (status.status === 'error') {
                    clearInterval(pollInterval);
                    reject(new Error(status.error || 'Error en el procesamiento'));
                    return;
                } else if (status.status === 'processing') {
                    lastProcessingTime = Date.now();
                } else if (status.status === 'idle' && (Date.now() - lastProcessingTime) > 5000) {
                    clearInterval(pollInterval);
                    reject(new Error('El procesamiento se interrumpió inesperadamente. Intentá de nuevo.'));
                    return;
                }

                if (Date.now() - startTime > timeoutMs) {
                    clearInterval(pollInterval);
                    reject(new Error('Timeout: el procesamiento tardó demasiado. Intentá de nuevo.'));
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
 * @param {string|null} clasificacion - 'moneda', 'region', o 'sector'. Si es null, usa la última procesada.
 */
export async function getValidationResults(clasificacion = null) {
    try {
        const url = clasificacion
            ? `${API_BASE_URL}/api/results/validation?clasificacion=${encodeURIComponent(clasificacion)}`
            : `${API_BASE_URL}/api/results/validation`;
        const response = await fetch(url, {
            headers: authHeaders(),
        });
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
        const response = await fetch(`${API_BASE_URL}/api/results/exports/${exportType}`, {
            headers: authHeaders(),
        });
        return await handleResponse(response);
    } catch (error) {
        console.error(`Error al obtener export ${exportType}:`, error);
        throw error;
    }
}

/**
 * Obtener el detalle de composición de un instrumento (breakdowns antigua y nueva)
 * @param {Number} instrumentId - ID del instrumento
 * @param {string|null} clasificacion - 'moneda', 'region', 'sector'. null = usa la última procesada.
 */
export async function getInstrumentDetail(instrumentId, clasificacion = null) {
    try {
        const url = clasificacion
            ? `${API_BASE_URL}/api/instrument/${instrumentId}/detail?clasificacion=${encodeURIComponent(clasificacion)}`
            : `${API_BASE_URL}/api/instrument/${instrumentId}/detail`;
        const response = await fetch(url, {
            headers: authHeaders(),
        });
        return await handleResponse(response);
    } catch (error) {
        console.error(`Error al obtener detalle del instrumento ${instrumentId}:`, error);
        throw error;
    }
}

/**
 * Descargar un archivo CSV de export
 *
 * @param {String} exportType - Tipo de export: 'balanceados', 'no_balanceados', 'con_cambios', 'sin_datos'
 * @param {String} clasificacion - 'moneda', 'region', 'sector'
 */
export async function downloadExport(exportType, clasificacion = null) {
    try {
        const params = clasificacion ? `?clasificacion=${encodeURIComponent(clasificacion)}` : '';
        const response = await fetch(`${API_BASE_URL}/api/download/${exportType}${params}`, {
            headers: authHeaders(),
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.message || 'Error al descargar archivo');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `export_${exportType}.xlsx`;
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
 * @param {String} exportType - Tipo de export
 * @param {Array} instrumentIds - Array de IDs de instrumentos
 * @param {String} clasificacion - 'moneda', 'region', 'sector'
 */
export async function downloadFilteredExport(exportType, instrumentIds, clasificacion = null) {
    try {
        const params = clasificacion ? `?clasificacion=${encodeURIComponent(clasificacion)}` : '';
        const response = await fetch(`${API_BASE_URL}/api/download-filtered/${exportType}${params}`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ instrument_ids: instrumentIds }),
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.message || 'Error al descargar archivo filtrado');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `export_${exportType}_filtrado.xlsx`;
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
            headers: authHeaders(),
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
        if (onProgress) onProgress({ stage: 'upload', progress: 0, message: 'Subiendo archivos...' });
        const uploadResult = await uploadFiles(files);

        if (uploadResult.status === 'error') {
            throw new Error(uploadResult.message);
        }

        if (onProgress) onProgress({ stage: 'process', progress: 0, message: 'Iniciando procesamiento...' });
        const processResult = await startProcessing();

        const finalStatus = await pollProcessingStatus((status) => {
            if (onProgress) {
                onProgress({
                    stage: 'processing',
                    progress: status.progress,
                    message: status.message,
                    status: status.status,
                });
            }
        });

        return finalStatus;
    } catch (error) {
        console.error('Error en flujo completo:', error);
        throw error;
    }
}

// ==================== REVISIONES ====================

/**
 * Obtener las revisiones guardadas para una clasificación.
 * @param {string} clasificacion - 'moneda', 'region', 'sector'
 */
export async function getReviews(clasificacion) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/reviews/${encodeURIComponent(clasificacion)}`, {
            headers: authHeaders(),
        });
        return await handleResponse(response);
    } catch (error) {
        console.error('Error al obtener revisiones:', error);
        throw error;
    }
}

/**
 * Guardar las revisiones de una clasificación en el servidor.
 * @param {string} clasificacion - 'moneda', 'region', 'sector'
 * @param {object} revisiones - Mapa { ID: 'Validado' | 'Rechazado' }
 */
export async function saveReviews(clasificacion, revisiones) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/reviews/${encodeURIComponent(clasificacion)}`, {
            method: 'PUT',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ revisiones }),
        });
        return await handleResponse(response);
    } catch (error) {
        console.error('Error al guardar revisiones:', error);
        throw error;
    }
}

// ==================== HISTORIAL ======================================

/**
 * Obtener la lista de entradas del historial (solo encabezados).
 */
export async function getHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/history`, {
            headers: authHeaders(),
        });
        return await handleResponse(response);
    } catch (error) {
        console.error('Error al obtener historial:', error);
        throw error;
    }
}

/**
 * Obtener el detalle completo de una entrada del historial.
 * @param {string} entryId - ID de la entrada
 */
export async function getHistoryDetail(entryId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/history/${encodeURIComponent(entryId)}`, {
            headers: authHeaders(),
        });
        return await handleResponse(response);
    } catch (error) {
        console.error('Error al obtener detalle del historial:', error);
        throw error;
    }
}

/**
 * Guardar la validación actual en el historial.
 * @param {{ label?: string, clasificacion: string, summary: object, revisiones: object }} data
 */
export async function saveToHistory(data) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/history`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(data),
        });
        return await handleResponse(response);
    } catch (error) {
        console.error('Error al guardar en historial:', error);
        throw error;
    }
}

/**
 * Eliminar una entrada del historial.
 * @param {string} entryId - ID de la entrada a eliminar
 */
export async function deleteHistoryEntry(entryId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/history/${encodeURIComponent(entryId)}`, {
            method: 'DELETE',
            headers: authHeaders(),
        });
        return await handleResponse(response);
    } catch (error) {
        console.error('Error al eliminar del historial:', error);
        throw error;
    }
}

export default {
    login,
    logout,
    isAuthenticated,
    getToken,
    checkHealth,
    uploadFiles,
    startProcessing,
    getProcessingStatus,
    pollProcessingStatus,
    getValidationResults,
    getAvailableResults,
    getExportData,
    downloadExport,
    downloadFilteredExport,
    resetProcessing,
    uploadAndProcess,
    getHistory,
    getHistoryDetail,
    saveToHistory,
    deleteHistoryEntry,
    getReviews,
    saveReviews,
};

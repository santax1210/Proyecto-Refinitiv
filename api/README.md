# API Flask - Validación de Allocations

API REST para conectar el frontend React con el pipeline de validación de allocations en Python.

## Instalación

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Uso

### Iniciar el servidor:
```bash
python app.py
```

El servidor estará disponible en `http://localhost:5000`

## Endpoints

### Health Check
```
GET /api/health
```
Verifica que la API esté funcionando.

### Subir Archivos
```
POST /api/upload
Content-Type: multipart/form-data

Body:
- posiciones: archivo CSV
- instruments: archivo CSV
- allocations_nuevas: archivo CSV
- allocations_antiguas: archivo CSV
```

### Ejecutar Pipeline
```
POST /api/process
```
Inicia el procesamiento del pipeline en background.

### Ver Estado
```
GET /api/status
```
Retorna el estado actual del procesamiento (idle, processing, completed, error).

### Obtener Resultados
```
GET /api/results/validation
```
Retorna los datos procesados para mostrar en la tabla de validación.

### Obtener Export Específico
```
GET /api/results/exports/<tipo>
```
Tipos: balanceados, no_balanceados, con_cambios, sin_datos

### Descargar CSV
```
GET /api/download/<tipo>
```
Descarga el archivo CSV del export especificado.

### Reiniciar Estado
```
DELETE /api/reset
```
Limpia el estado del procesamiento.

## Arquitectura

```
Frontend (React)  →  API Flask  →  Pipeline Python
    :5173              :5000         run_pipeline.py
```

## Flujo de Trabajo

1. Usuario sube archivos desde el frontend
2. Frontend envía archivos a `/api/upload`
3. API guarda archivos en `data/raw/`
4. Frontend solicita procesamiento con `/api/process`
5. API ejecuta pipeline en background
6. Frontend hace polling a `/api/status` para ver progreso
7. Cuando status = "completed", frontend consulta `/api/results/validation`
8. Frontend muestra datos en tablas y gráficos

## Configuración

- **Puerto**: 5000
- **CORS**: Habilitado para `http://localhost:5173` (Vite dev server)
- **Max file size**: 50MB por archivo
- **Data folders**:
  - Upload: `data/raw/`
  - Processed: `data/processed/`
  - Exports: `data/exports/`

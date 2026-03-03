"""
API Flask para el sistema de validación de allocations.

Este servidor provee endpoints REST para:
- Subir archivos CSV
- Ejecutar el pipeline de validación
- Consultar resultados procesados
- Descargar exports generados
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
import threading
import time
from datetime import datetime

# Crear app Flask
app = Flask(__name__)

# Configurar CORS para permitir requests desde el frontend React
CORS(app, origins=['http://localhost:5173', 'http://localhost:5174'])

# Configuración
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'raw')
app.config['PROCESSED_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'processed')
app.config['EXPORTS_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'exports')

# Estado global del procesamiento (en producción usar Redis o DB)
processing_state = {
    'status': 'idle',  # idle, processing, completed, error
    'progress': 0,
    'message': '',
    'job_id': None,
    'start_time': None,
    'end_time': None,
    'error': None
}

# Archivos esperados
REQUIRED_FILES = {
    'posiciones': 'posiciones.csv',
    'instruments': 'instruments.csv',
    'allocations_nuevas': 'allocations_nuevas.csv',
    'allocations_antiguas': 'allocations_currency.csv'
}

# ==================== RUTAS ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verificar que la API está funcionando."""
    return jsonify({
        'status': 'ok',
        'message': 'API Flask funcionando correctamente',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """
    Subir archivos CSV para procesamiento.
    
    Espera archivos en multipart/form-data con nombres:
    - posiciones
    - instruments
    - allocations_nuevas
    - allocations_antiguas
    """
    try:
        # Verificar que se enviaron archivos
        if not request.files:
            return jsonify({
                'status': 'error',
                'message': 'No se enviaron archivos'
            }), 400
        
        uploaded_files = []
        missing_files = []
        
        # Crear directorio si no existe
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Procesar cada archivo esperado
        for file_key, file_name in REQUIRED_FILES.items():
            if file_key in request.files:
                file = request.files[file_key]
                if file.filename:
                    # Guardar con nombre esperado
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
                    file.save(file_path)
                    
                    # Verificar tamaño
                    file_size = os.path.getsize(file_path)
                    uploaded_files.append({
                        'name': file_name,
                        'size': f"{file_size / (1024*1024):.2f} MB",
                        'path': file_path
                    })
            else:
                missing_files.append(file_name)
        
        if missing_files:
            return jsonify({
                'status': 'warning',
                'message': f'Faltan archivos: {", ".join(missing_files)}',
                'uploaded': uploaded_files,
                'missing': missing_files
            }), 206
        
        return jsonify({
            'status': 'success',
            'message': f'Se subieron {len(uploaded_files)} archivos correctamente',
            'files': uploaded_files,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error al subir archivos: {str(e)}'
        }), 500

@app.route('/api/process', methods=['POST'])
def process_pipeline():
    """
    Ejecutar el pipeline de validación en background.
    """
    global processing_state
    
    try:
        # Verificar que no haya un proceso en curso
        if processing_state['status'] == 'processing':
            return jsonify({
                'status': 'error',
                'message': 'Ya hay un procesamiento en curso'
            }), 409
        
        # Verificar que los archivos existen
        missing = []
        for file_name in REQUIRED_FILES.values():
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
            if not os.path.exists(file_path):
                missing.append(file_name)
        
        if missing:
            return jsonify({
                'status': 'error',
                'message': f'Faltan archivos requeridos: {", ".join(missing)}'
            }), 400
        
        # Iniciar procesamiento en thread separado
        job_id = f"job_{int(time.time())}"
        processing_state.update({
            'status': 'processing',
            'progress': 0,
            'message': 'Iniciando pipeline...',
            'job_id': job_id,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'error': None
        })
        
        # Ejecutar en thread
        thread = threading.Thread(target=run_pipeline_background)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'success',
            'message': 'Pipeline iniciado',
            'job_id': job_id
        }), 202
        
    except Exception as e:
        processing_state['status'] = 'error'
        processing_state['error'] = str(e)
        return jsonify({
            'status': 'error',
            'message': f'Error al iniciar pipeline: {str(e)}'
        }), 500

def run_pipeline_background():
    """Ejecutar el pipeline en background (llamado por thread)."""
    global processing_state
    
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        
        from src.extractors.load_instruments import load_df_instruments
        from src.extractors.load_allocations import load_allocations_nuevas, load_allocations_antiguas
        from src.logic.clasificacion import ejecutar_pipeline_completo
        
        # Actualizar progreso
        processing_state['progress'] = 10
        processing_state['message'] = 'Cargando instrumentos...'
        
        # Cargar datos
        pos_path = os.path.join(app.config['UPLOAD_FOLDER'], 'posiciones.csv')
        instr_path = os.path.join(app.config['UPLOAD_FOLDER'], 'instruments.csv')
        nuevas_path = os.path.join(app.config['UPLOAD_FOLDER'], 'allocations_nuevas.csv')
        antiguas_path = os.path.join(app.config['UPLOAD_FOLDER'], 'allocations_currency.csv')
        
        df_instruments = load_df_instruments(pos_path, instr_path)
        
        processing_state['progress'] = 30
        processing_state['message'] = 'Cargando allocations nuevas...'
        
        df_nuevas = load_allocations_nuevas(df_instruments, nuevas_path, umbral=0.9)
        
        processing_state['progress'] = 50
        processing_state['message'] = 'Cargando allocations antiguas...'
        
        df_antiguas = load_allocations_antiguas(df_instruments, antiguas_path)
        
        processing_state['progress'] = 70
        processing_state['message'] = 'Ejecutando pipeline de clasificación...'
        
        # Ejecutar pipeline completo
        resultados = ejecutar_pipeline_completo(df_instruments, df_nuevas, df_antiguas)
        
        processing_state['progress'] = 90
        processing_state['message'] = 'Guardando resultados...'
        
        # Guardar resultados procesados
        os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
        os.makedirs(app.config['EXPORTS_FOLDER'], exist_ok=True)
        
        # Guardar dataframes
        resultados['df_final'].to_csv(
            os.path.join(app.config['PROCESSED_FOLDER'], 'df_final.csv'),
            index=False,
            sep=';',
            encoding='utf-8'
        )
        
        # Guardar exports
        for key, df in resultados['exports'].items():
            export_path = os.path.join(app.config['EXPORTS_FOLDER'], f'export_{key}.csv')
            df.to_csv(export_path, index=False, sep=';', encoding='utf-8')
        
        # Guardar resumen como JSON para fácil acceso desde el frontend
        summary = {
            'total_instrumentos': len(resultados['df_final']),
            'balanceados': len(resultados['exports']['balanceados']),
            'no_balanceados': len(resultados['exports']['no_balanceados']),
            'con_cambios': len(resultados['exports']['con_cambios']),
            'sin_datos': len(resultados['exports']['sin_datos']),
            'timestamp': datetime.now().isoformat()
        }
        
        with open(os.path.join(app.config['PROCESSED_FOLDER'], 'summary.json'), 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Completar
        processing_state.update({
            'status': 'completed',
            'progress': 100,
            'message': 'Pipeline completado exitosamente',
            'end_time': datetime.now().isoformat()
        })
        
    except Exception as e:
        processing_state.update({
            'status': 'error',
            'progress': 0,
            'message': 'Error durante el procesamiento',
            'error': str(e),
            'end_time': datetime.now().isoformat()
        })

@app.route('/api/status', methods=['GET'])
def get_status():
    """Obtener el estado actual del procesamiento."""
    return jsonify(processing_state)

@app.route('/api/results/validation', methods=['GET'])
def get_validation_results():
    """
    Obtener datos de validación para la tabla.
    
    Retorna el df_final procesado con columnas mapeadas para el frontend.
    """
    try:
        df_final_path = os.path.join(app.config['PROCESSED_FOLDER'], 'df_final.csv')
        
        if not os.path.exists(df_final_path):
            return jsonify({
                'status': 'error',
                'message': 'No hay datos procesados. Ejecuta el pipeline primero.'
            }), 404
        
        import pandas as pd
        df = pd.read_csv(df_final_path, sep=';', encoding='utf-8')
        
        # El pipeline ya genera todas las columnas necesarias
        # Solo enviamos los datos tal cual sin transformaciones
        
        # Convertir a formato JSON para el frontend
        # Reemplazar NaN con None para evitar errores de serialización JSON
        df = df.astype(object).where(pd.notna(df), None)
        data = df.to_dict(orient='records')
        
        # Leer resumen si existe
        summary_path = os.path.join(app.config['PROCESSED_FOLDER'], 'summary.json')
        summary = {}
        if os.path.exists(summary_path):
            with open(summary_path, 'r') as f:
                summary = json.load(f)
        
        return jsonify({
            'status': 'success',
            'data': data,
            'summary': summary,
            'count': len(data)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error al leer resultados: {str(e)}'
        }), 500

@app.route('/api/results/exports/<export_type>', methods=['GET'])
def get_export_data(export_type):
    """
    Obtener datos de un export específico.
    
    export_type: balanceados, no_balanceados, con_cambios, sin_datos
    """
    try:
        export_path = os.path.join(app.config['EXPORTS_FOLDER'], f'export_{export_type}.csv')
        
        if not os.path.exists(export_path):
            return jsonify({
                'status': 'error',
                'message': f'No existe el export: {export_type}'
            }), 404
        
        import pandas as pd
        df = pd.read_csv(export_path, sep=';', encoding='utf-8')
        
        # Los exports ya tienen las columnas correctas del pipeline
        # Se envían tal cual sin transformaciones
        
        # Reemplazar NaN con None para evitar errores de serialización JSON
        df = df.astype(object).where(pd.notna(df), None)
        
        return jsonify({
            'status': 'success',
            'data': df.to_dict(orient='records'),
            'count': len(df)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error al leer export: {str(e)}'
        }), 500

@app.route('/api/download/<export_type>', methods=['GET'])
def download_export(export_type):
    """
    Descargar un archivo CSV de export.
    
    export_type: balanceados, no_balanceados, con_cambios, sin_datos
    """
    try:
        export_path = os.path.join(app.config['EXPORTS_FOLDER'], f'export_{export_type}.csv')
        
        if not os.path.exists(export_path):
            return jsonify({
                'status': 'error',
                'message': f'No existe el export: {export_type}'
            }), 404
        
        return send_file(
            export_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'export_{export_type}.csv'
        )
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error al descargar archivo: {str(e)}'
        }), 500

@app.route('/api/reset', methods=['DELETE'])
def reset_data():
    """Limpiar datos temporales y reiniciar estado."""
    global processing_state
    
    try:
        processing_state = {
            'status': 'idle',
            'progress': 0,
            'message': '',
            'job_id': None,
            'start_time': None,
            'end_time': None,
            'error': None
        }
        
        return jsonify({
            'status': 'success',
            'message': 'Estado reiniciado correctamente'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error al reiniciar: {str(e)}'
        }), 500

# ==================== ERROR HANDLERS ====================

@app.errorhandler(413)
def request_entity_too_large(error):
    """Error cuando el archivo es muy grande."""
    return jsonify({
        'status': 'error',
        'message': 'El archivo es demasiado grande. Máximo 50MB por archivo.'
    }), 413

@app.errorhandler(404)
def not_found(error):
    """Error cuando la ruta no existe."""
    return jsonify({
        'status': 'error',
        'message': 'Endpoint no encontrado'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Error interno del servidor."""
    return jsonify({
        'status': 'error',
        'message': 'Error interno del servidor'
    }), 500

# ==================== MAIN ====================

if __name__ == '__main__':
    # Crear directorios necesarios
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
    os.makedirs(app.config['EXPORTS_FOLDER'], exist_ok=True)
    
    print("\n" + "="*60)
    print(" API FLASK - Validación de Allocations ".center(60, "="))
    print("="*60)
    print("\nServidor corriendo en: http://localhost:5000")
    print(f"Archivos raw: {app.config['UPLOAD_FOLDER']}")
    print(f"Archivos procesados: {app.config['PROCESSED_FOLDER']}")
    print(f"Exports: {app.config['EXPORTS_FOLDER']}")
    print(f"\nEndpoints disponibles:")
    print(f"   - GET  /api/health")
    print(f"   - POST /api/upload")
    print(f"   - POST /api/process")
    print(f"   - GET  /api/status")
    print(f"   - GET  /api/results/validation")
    print(f"   - GET  /api/results/exports/<type>")
    print(f"   - GET  /api/download/<type>")
    print(f"   - DELETE /api/reset")
    print("="*60 + "\n")
    
    # Correr servidor (debug mode solo en desarrollo)
    app.run(debug=True, host='0.0.0.0', port=5000)

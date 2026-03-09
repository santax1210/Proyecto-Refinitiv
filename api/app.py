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

# Configuración de archivos según clasificación
def get_file_config(clasificacion, upload_folder):
    """Devuelve {file_key: ruta_destino} según la clasificación seleccionada."""
    region_folder = os.path.join(upload_folder, 'region')
    if clasificacion == 'region':
        return {
            'posiciones':          os.path.join(upload_folder, 'posiciones.csv'),
            'instruments':         os.path.join(upload_folder, 'instruments.csv'),
            'allocations_nuevas':  os.path.join(region_folder, 'allocations_nuevas_region.csv'),
            'allocations_antiguas': os.path.join(region_folder, 'allocations_region.csv'),
        }
    else:  # moneda (default)
        return {
            'posiciones':          os.path.join(upload_folder, 'posiciones.csv'),
            'instruments':         os.path.join(upload_folder, 'instruments.csv'),
            'allocations_nuevas':  os.path.join(upload_folder, 'allocations_nuevas.csv'),
            'allocations_antiguas': os.path.join(upload_folder, 'allocations_currency.csv'),
        }

def get_result_paths(clasificacion=None):
    """Devuelve (proc_folder, exp_folder, df_final_name) según la clasificación procesada."""
    if clasificacion is None:
        clasificacion = processing_state.get('clasificacion', 'moneda')
    if clasificacion == 'region':
        return (
            os.path.join(app.config['PROCESSED_FOLDER'], 'region'),
            os.path.join(app.config['EXPORTS_FOLDER'], 'region'),
            'df_final_region.csv',
        )
    else:
        return (
            app.config['PROCESSED_FOLDER'],
            app.config['EXPORTS_FOLDER'],
            'df_final.csv',
        )

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

        # Leer clasificación y normalizar
        clasificacion = request.form.get('clasificacion', 'moneda').strip().lower()
        if 'regi' in clasificacion:
            clasificacion = 'region'

        # Crear directorios necesarios
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'region'), exist_ok=True)

        # Guardar clasificación para el endpoint /process
        processing_state['last_clasificacion'] = clasificacion

        # Obtener rutas de destino según clasificación
        file_config = get_file_config(clasificacion, app.config['UPLOAD_FOLDER'])

        # Procesar cada archivo
        for file_key, file_path in file_config.items():
            if file_key in request.files:
                file = request.files[file_key]
                if file.filename:
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    file.save(file_path)
                    file_size = os.path.getsize(file_path)
                    uploaded_files.append({
                        'name': os.path.basename(file_path),
                        'size': f"{file_size / (1024*1024):.2f} MB",
                        'path': file_path
                    })
            else:
                missing_files.append(os.path.basename(file_path))
        
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
        
        # Leer clasificación (del body o de la última subida)
        data = request.get_json() or {}
        clasificacion = data.get('clasificacion', processing_state.get('last_clasificacion', 'moneda')).strip().lower()
        if 'regi' in clasificacion:
            clasificacion = 'region'

        # Verificar que los archivos existen
        file_config = get_file_config(clasificacion, app.config['UPLOAD_FOLDER'])
        missing = []
        for file_path in file_config.values():
            if not os.path.exists(file_path):
                missing.append(os.path.basename(file_path))
        
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
            'clasificacion': clasificacion,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'error': None
        })
        
        # Ejecutar en thread
        thread = threading.Thread(target=run_pipeline_background, args=(clasificacion,))
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

def run_pipeline_background(clasificacion='moneda'):
    """Ejecutar el pipeline en background (llamado por thread)."""
    global processing_state
    
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

        processing_state['progress'] = 10
        processing_state['message'] = 'Cargando instrumentos...'

        file_config = get_file_config(clasificacion, app.config['UPLOAD_FOLDER'])
        pos_path     = file_config['posiciones']
        instr_path   = file_config['instruments']
        nuevas_path  = file_config['allocations_nuevas']
        antiguas_path = file_config['allocations_antiguas']

        if clasificacion == 'region':
            from src.extractors.region.load_instruments_region import load_instruments_region
            from src.extractors.region.load_allocations_region import (
                load_allocations_nuevas_region, load_allocations_antiguas_region
            )
            from src.logic.region.clasificacion_region import ejecutar_pipeline_completo_region

            df_instruments = load_instruments_region(pos_path, instr_path)

            processing_state['progress'] = 30
            processing_state['message'] = 'Cargando allocations nuevas...'
            df_nuevas = load_allocations_nuevas_region(df_instruments, nuevas_path, umbral=0.9)

            processing_state['progress'] = 50
            processing_state['message'] = 'Cargando allocations antiguas...'
            df_antiguas = load_allocations_antiguas_region(df_instruments, antiguas_path)

            processing_state['progress'] = 70
            processing_state['message'] = 'Ejecutando pipeline de región...'
            resultados = ejecutar_pipeline_completo_region(df_instruments, df_nuevas, df_antiguas)

            exports       = resultados['exports']
            df_final      = resultados['df_final']
            proc_folder   = os.path.join(app.config['PROCESSED_FOLDER'], 'region')
            exp_folder    = os.path.join(app.config['EXPORTS_FOLDER'],   'region')
            df_final_name = 'df_final_region.csv'

        else:  # moneda
            from src.extractors.moneda.load_instruments import load_df_instruments
            from src.extractors.moneda.load_allocations import load_allocations_nuevas, load_allocations_antiguas
            from src.logic.moneda.clasificacion import ejecutar_pipeline_completo
        
            df_instruments = load_df_instruments(pos_path, instr_path)

            processing_state['progress'] = 30
            processing_state['message'] = 'Cargando allocations nuevas...'
            df_nuevas = load_allocations_nuevas(df_instruments, nuevas_path, umbral=0.9)

            processing_state['progress'] = 50
            processing_state['message'] = 'Cargando allocations antiguas...'
            df_antiguas = load_allocations_antiguas(df_instruments, antiguas_path)

            processing_state['progress'] = 70
            processing_state['message'] = 'Ejecutando pipeline de clasificación...'
            resultados = ejecutar_pipeline_completo(df_instruments, df_nuevas, df_antiguas)

            exports       = resultados['exports']
            df_final      = resultados['df_final']
            proc_folder   = app.config['PROCESSED_FOLDER']
            exp_folder    = app.config['EXPORTS_FOLDER']
            df_final_name = 'df_final.csv'

        # ── Guardar resultados ──
        processing_state['progress'] = 90
        processing_state['message'] = 'Guardando resultados...'

        os.makedirs(proc_folder, exist_ok=True)
        os.makedirs(exp_folder,  exist_ok=True)

        df_final.to_csv(os.path.join(proc_folder, df_final_name), index=False, sep=';', encoding='utf-8')

        for key, df_exp in exports.items():
            df_exp.to_csv(os.path.join(exp_folder, f'export_{key}.csv'), index=False, sep=';', encoding='utf-8')

        summary = {
            'total_instrumentos': len(df_final),
            'balanceados':   len(exports.get('balanceados',   [])),
            'no_balanceados': len(exports.get('no_balanceados', [])),
            'con_cambios':   len(exports.get('con_cambios',   [])),
            'sin_datos':     len(exports.get('sin_datos',     [])),
            'clasificacion': clasificacion,
            'timestamp': datetime.now().isoformat()
        }

        with open(os.path.join(proc_folder, 'summary.json'), 'w') as f:
            json.dump(summary, f, indent=2)

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
        proc_folder, _, df_final_name = get_result_paths()
        df_final_path = os.path.join(proc_folder, df_final_name)
        
        if not os.path.exists(df_final_path):
            return jsonify({
                'status': 'error',
                'message': 'No hay datos procesados. Ejecuta el pipeline primero.'
            }), 404
        
        import pandas as pd
        df = pd.read_csv(df_final_path, sep=';', encoding='utf-8')
        
        df = df.astype(object).where(pd.notna(df), None)
        data = df.to_dict(orient='records')
        
        summary_path = os.path.join(proc_folder, 'summary.json')
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
        _, exp_folder, _ = get_result_paths()
        export_path = os.path.join(exp_folder, f'export_{export_type}.csv')
        
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
        _, exp_folder, _ = get_result_paths()
        export_path = os.path.join(exp_folder, f'export_{export_type}.csv')
        
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

@app.route('/api/download-filtered/<export_type>', methods=['POST'])
def download_filtered_export(export_type):
    """
    Descargar un archivo CSV de export filtrado por IDs de instrumentos.
    
    Body (JSON):
    {
        "instrument_ids": [23, 31, 32, ...]
    }
    
    export_type: balanceados, no_balanceados, con_cambios, sin_datos
    """
    try:
        # Obtener IDs del body
        data = request.get_json()
        if not data or 'instrument_ids' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Se requiere "instrument_ids" en el body'
            }), 400
        
        instrument_ids = data['instrument_ids']
        
        # Si no hay IDs, descargar el archivo completo
        if not instrument_ids:
            return download_export(export_type)
        
        # Convertir IDs a set para búsqueda rápida
        id_set = set(map(str, instrument_ids))
        
        # Ruta del archivo export original
        _, exp_folder, _ = get_result_paths()
        export_path = os.path.join(exp_folder, f'export_{export_type}.csv')
        
        if not os.path.exists(export_path):
            return jsonify({
                'status': 'error',
                'message': f'No existe el export: {export_type}'
            }), 404
        
        # Leer y filtrar el CSV
        import csv
        from io import StringIO
        
        filtered_rows = []
        with open(export_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            header = next(reader)  # Guardar encabezado
            filtered_rows.append(header)
            
            # Filtrar filas por ID
            for row in reader:
                if row and row[0] in id_set:  # Primera columna es ID
                    filtered_rows.append(row)
        
        # Crear CSV filtrado en memoria
        output = StringIO()
        writer = csv.writer(output, delimiter=';', lineterminator='\n')
        writer.writerows(filtered_rows)
        csv_content = output.getvalue()
        output.close()
        
        # Crear respuesta con el CSV filtrado
        from flask import Response
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=export_{export_type}_filtrado.csv'
            }
        )
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error al descargar archivo filtrado: {str(e)}'
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

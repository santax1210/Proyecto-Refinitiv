# Proyecto: Conciliación de Datos Financieros

Este sistema automatiza la validación y comparación de **Allocations de Moneda** para instrumentos financieros, permitiendo transicionar de datos legados (antiguos) a nuevas definiciones validadas por dominancia.

## 🚀 Objetivo
Analizar los datos internos de distintas fuentes para validar las **nuevas allocations** mediante una lógica de dominancia del 90%, escalando los porcentajes al 100% y comparando el resultado contra las allocations antiguas para generar los reportes de actualización.

---

## 🏗️ Estructura del Proyecto
```text
allocations_validation/
├── data/
│   ├── raw/                    # Archivos fuente (CSV)
│   │   ├── posiciones.csv
│   │   ├── instruments.csv
│   │   ├── allocations_nuevas.csv
│   │   └── allocations_currency.csv
│   ├── processed/              # DataFrames intermedios para análisis técnico
│   │   ├── df_instruments.csv
│   │   ├── allocations_nuevas_merged.csv
│   │   ├── allocations_nuevas_con_dominancia.csv
│   │   ├── allocations_antiguas.csv (incluye Pct_dominancia)
│   │   └── df_final*.csv
│   └── exports/                # Archivos finales para usuario
│       ├── export_balanceados.csv
│       ├── export_no_balanceados.csv
│       └── export_con_cambios.csv
├── src/
│   ├── extractors/             # Módulos de carga y cruce de datos
│   │   ├── load_instruments.py     # Carga maestro + posiciones
│   │   └── load_allocations.py     # Carga allocations nuevas/antiguas
│   ├── logic/                  # Lógica de negocio modular
│   │   ├── escalado.py             # Escalado de porcentajes al 100%
│   │   ├── dominancia_nuevas.py    # Cálculo dominancia nuevas allocations
│   │   ├── dominancia_antiguas.py  # Cálculo dominancia antiguas allocations
│   │   ├── crear_df_final.py       # Ensamblaje del dataframe final
│   │   ├── clasificacion.py        # Orquestador principal del pipeline
│   │   └── README.md               # Documentación de arquitectura
│   └── utils/                  # Funciones auxiliares
├── dashboard-financiero/       # Dashboard React para visualización
│   ├── src/
│   │   ├── components/
│   │   └── pages/
│   └── package.json
├── tests/                      # Scripts de validación
│   ├── test_carga_archivos.py
│   └── test_creacion_dataframes.py
├── run_pipeline.py             # Script principal de ejecución
├── requirements.txt            # Dependencias Python
├── .gitignore
└── README.md                   # Este archivo
```

---

## 🔄 Flujo del Pipeline

### Arquitectura Modular
El pipeline está organizado en módulos especializados para facilitar mantenimiento y testing:

```
┌─────────────────────────────────────────────────────────────────┐
│  FASE 1: EXTRACCIÓN Y FILTRADO                                  │
└─────────────────────────────────────────────────────────────────┘
    ↓
  load_instruments.py
    • Cruza posiciones × maestro de instrumentos por ID
    • Filtra: Fecha proceso > 01/06/2025
    • Filtra: Tipos de instrumento (C02, C03, C04, C09, C10, C14)
    • Genera: df_instruments [ID, Nombre, País, Tipo, RIC, Isin, Cusip, SubMoneda]
    ↓
  load_allocations.py
    • Cruza df_instruments × allocations_nuevas (RIC → Isin → Cusip)
    • Filtra: classif == 'currency'
    • Genera: allocations_nuevas [ID, Nombre, instrument, class, percentage, date]
    
    • Cruza df_instruments × allocations_currency por ID
    • Genera: allocations_antiguas [ID, Nombre, SubMoneda, CLP, USD, EUR...]

┌─────────────────────────────────────────────────────────────────┐
│  FASE 2: CLASIFICACIÓN Y CÁLCULO DE DOMINANCIA                  │
└─────────────────────────────────────────────────────────────────┘
    ↓
  escalado.py
    • Escala porcentajes al 100% proporcionalmente
    ↓
  dominancia_nuevas.py
    • Calcula dominancia por instrumento (umbral 90%)
    • Genera columnas:
      - moneda_nueva: "Balanceado" o moneda específica (USD, CLP...)
      - pct_dominancia_nuevo: "USD 95.5%"
      - pct_escalado: Suma post-escalado (validación)
      - pct_original: Suma pre-escalado
    ↓
  dominancia_antiguas.py
    • Identifica moneda dominante en formato wide
    • Genera columnas:
      - Pct_dominancia: "USD 80.5%"
      - moneda_antigua, pct_antigua

┌─────────────────────────────────────────────────────────────────┐
│  FASE 3: COMPARACIÓN Y EXPORTACIÓN                              │
└─────────────────────────────────────────────────────────────────┘
    ↓
  crear_df_final.py
    • Consolida todos los dataframes
    • Detecta cambios entre moneda_nueva vs moneda_antigua
    • Genera: df_final [Nombre, ID, Tipo, SubMoneda, moneda_nueva, 
                        pct_dominancia_nuevo, moneda_antigua, Cambio]
    • Filtra vistas especializadas:
      - df_balanceados
      - df_no_balanceados
      - df_con_cambios
    ↓
  EXPORTACIÓN
    • data/processed/   → Archivos técnicos intermedios
    • data/exports/     → Archivos finales para usuario
```

### Detalle de Transformaciones Principales

1. **Extracción y Maestro de Instrumentos**
   - Se cruzan las `posiciones` con el `maestro de instrumentos` por `ID`
   - **Filtros**: Fecha de proceso > `01/06/2025` y tipos de instrumento específicos

2. **Cruce de Nuevas Allocations**
   - Se unen los instrumentos resultantes con `allocations_nuevas.csv`
   - **Matching**: Se intenta secuencialmente por `RIC`, luego `Isin` y finalmente `Cusip`
   - **Filtro Interno**: Solo registros con `classif == 'currency'`

3. **Lógica de Clasificación (Dominancia 90%)**
   - **Escalado**: Los porcentajes originales se escalan proporcionalmente para que la suma total sea exactamente **100%**
   - **Dominancia**: Si una moneda tiene **>= 90%** del total escalado, el instrumento se clasifica con esa moneda (ej: `USD`). De lo contrario, se marca como `Balanceado`

4. **Cruce de Allocations Antiguas**
   - Se extrae la moneda predominante actual de los registros históricos para permitir la comparación

5. **Comparación Final y Exportación**
   - Se genera un reporte consolidado (`df_final.csv`) indicando si hubo cambio
   - Se segregan los resultados en tres archivos:
     - `export_balanceados.csv`: Instrumentos sin moneda dominante
     - `export_no_balanceados.csv`: Instrumentos con moneda específica
     - `export_con_cambios.csv`: Instrumentos cuya clasificación cambió

---

## 🛠️ Tecnologías Utilizadas

### Backend (Python)
- **Lenguaje**: Python 3.8+
- **Librería Principal**: Pandas (Manipulación de datos)
- **Módulos Nativos**: `csv` (parsing robusto de archivos inconsistentes)

### Frontend (Dashboard)
- **Framework**: React + Vite
- **UI Components**: Custom components
- **Routing**: React Router

---

## 📦 Instalación y Configuración

### Prerrequisitos
- Python 3.8 o superior
- Node.js 16+ (para el dashboard)
- Git

### 1. Clonar el Repositorio
```bash
git clone <repository-url>
cd allocations_validation
```

### 2. Configurar Entorno Virtual (Recomendado)

**⚠️ IMPORTANTE para despliegue en servidores:**

El uso de un entorno virtual es **esencial** para:
- ✅ Aislar dependencias del sistema
- ✅ Garantizar versiones consistentes entre entornos
- ✅ Facilitar despliegue en múltiples servidores
- ✅ Evitar conflictos con otros proyectos Python

#### Windows (PowerShell)
```powershell
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Si hay problemas de permisos, ejecutar:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Linux/Mac
```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate
```

### 3. Instalar Dependencias Python
```bash
# Con el entorno virtual activado
pip install -r requirements.txt
```

### 4. Configurar Dashboard (Opcional)
```bash
cd dashboard-financiero
npm install
cd ..
```

### 5. Verificar Estructura de Datos
Asegúrate de que los archivos raw están en su lugar:
```
data/raw/
├── posiciones.csv
├── instruments.csv
├── allocations_nuevas.csv
└── allocations_currency.csv
```

---

## 🚀 Ejecución

### Opción 1: Pipeline Completo (Recomendado)
```bash
# Asegúrate de que el entorno virtual está activado
python run_pipeline.py
```

Este script ejecuta todo el flujo y genera:
- `data/processed/` → Archivos intermedios para inspección
- `data/exports/` → Archivos finales para el usuario

### Opción 2: Módulos Individuales

```bash
# Solo carga de instrumentos
python -m src.extractors.load_instruments

# Solo carga de allocations
python -m src.extractors.load_allocations

# Solo clasificación (requiere datos ya cargados)
python -m src.logic.clasificacion

# Probar módulos específicos
python -m src.logic.escalado
python -m src.logic.dominancia_nuevas
python -m src.logic.dominancia_antiguas
python -m src.logic.crear_df_final
```

### Opción 3: Dashboard de Visualización
```bash
cd dashboard-financiero
npm run dev
```

El dashboard estará disponible en `http://localhost:5173`

---

## 📊 DataFrames Generados

### df_instruments
**Origen**: Cruce de posiciones × maestro de instrumentos  
**Columnas**: ID, Nombre, Pais, Tipo instrumento, RIC, Isin, Cusip, SubMoneda

### allocations_nuevas
**Origen**: Cruce de df_instruments × allocations_nuevas.csv  
**Columnas**:
- ID, Nombre, instrument, class, percentage, date *(base)*
- moneda_nueva, pct_dominancia_nuevo, pct_escalado, pct_original *(calculadas)*

### allocations_antiguas
**Origen**: Cruce de df_instruments × allocations_currency.csv  
**Columnas**:
- ID, Nombre, SubMoneda *(de df_instruments)*
- Columnas de monedas con porcentajes: CLP, USD, EUR... *(del archivo raw)*
- Pct_dominancia *(calculada automáticamente)*  
  Formato: "MONEDA XX.XX%" (ejemplo: "USD 80.50%")

**Nota**: Este dataframe ya incluye Pct_dominancia calculada al momento de la carga, no requiere procesamiento adicional.

### df_final (Para UI)
**Origen**: Consolidación de todos los dataframes  
**Columnas**:
- Nombre, ID, Tipo instrumento, SubMoneda
- moneda_nueva, pct_dominancia_nuevo, pct_escalado, pct_original
- moneda_antigua, pct_dominancia_antigua
- Cambio *(Sí/No/Sin datos)*

---

## 🧪 Validación y Pruebas

### Tests Unitarios
El proyecto incluye tests para cada módulo:

```bash
# Test de carga de archivos
python tests/test_carga_archivos.py

# Test de creación de dataframes
python tests/test_creacion_dataframes.py

# Tests individuales de módulos (incluyen datos de ejemplo)
python -m src.logic.escalado
python -m src.logic.dominancia_nuevas
python -m src.logic.dominancia_antiguas
python -m src.logic.crear_df_final
```

### Validación Manual
Después de ejecutar el pipeline, revisa:
- `data/processed/df_final.csv` → Resultado principal
- `data/exports/` → Archivos segregados por tipo
- Logs en consola → Estadísticas y resumen ejecutivo

---

## 🖥️ Despliegue en Servidores

### Preparación para Producción

#### 1. Configurar Entorno en Servidor
```bash
# Conectar al servidor
ssh usuario@servidor

# Ir al directorio del proyecto
cd /path/to/allocations_validation

# Crear entorno virtual
python3 -m venv venv

# Activar entorno
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

#### 2. Transferir Datos Raw
```bash
# Desde tu máquina local (usar scp, sftp, o sistema de archivos compartido)
scp data/raw/*.csv usuario@servidor:/path/to/allocations_validation/data/raw/
```

#### 3. Ejecutar Pipeline
```bash
# En el servidor
python run_pipeline.py
```

#### 4. Recuperar Resultados
```bash
# Desde tu máquina local
scp -r usuario@servidor:/path/to/allocations_validation/data/exports/ ./resultados/
```

### Automatización con Cron (Linux)
```bash
# Editar crontab
crontab -e

# Ejecutar diariamente a las 6:00 AM
0 6 * * * cd /path/to/allocations_validation && /path/to/allocations_validation/venv/bin/python run_pipeline.py >> logs/pipeline.log 2>&1
```

### Automatización con Task Scheduler (Windows Server)
1. Abrir "Programador de tareas"
2. Crear tarea básica
3. Configurar:
   - **Programa**: `C:\path\to\venv\Scripts\python.exe`
   - **Argumentos**: `run_pipeline.py`
   - **Directorio**: `C:\path\to\allocations_validation`

---

## 📝 Buenas Prácticas

### Gestión de Entornos

#### Activar/Desactivar Entorno Virtual
```bash
# Activar
.\venv\Scripts\Activate.ps1    # Windows
source venv/bin/activate        # Linux/Mac

# Desactivar
deactivate
```

#### Actualizar Dependencias
```bash
# Si agregas nuevas librerías
pip freeze > requirements.txt
```

### Versionamiento de Datos
- Respalda `data/raw/` antes de cada ejecución
- Mantén un log de versiones de inputs:
```bash
# Ejemplo de backup
cp -r data/raw/ data/backups/raw_$(date +%Y%m%d)/
```

### Logs y Monitoreo
```bash
# Ejecutar con logging
python run_pipeline.py > logs/pipeline_$(date +%Y%m%d).log 2>&1

# Ver logs en tiempo real
tail -f logs/pipeline_*.log
```

---

## 📂 Estructura de Salidas

### data/processed/ (Técnico)
Archivos intermedios para análisis técnico y debugging:
- `df_instruments.csv` → Base de instrumentos filtrados
- `allocations_nuevas_merged.csv` → Allocations nuevas sin métricas
- `allocations_nuevas_con_dominancia.csv` → Allocations nuevas con métricas calculadas
- `allocations_antiguas.csv` → Allocations antiguas (ya incluye Pct_dominancia)
- `df_final.csv` → Consolidado completo
- `df_final_balanceados.csv` → Solo balanceados
- `df_final_no_balanceados.csv` → Solo no balanceados
- `df_final_con_cambios.csv` → Solo con cambios

### data/exports/ (Usuario Final)
Archivos finales listos para usuario:
- `export_balanceados.csv` → Instrumentos sin moneda dominante
- `export_no_balanceados.csv` → Instrumentos con moneda específica
- `export_con_cambios.csv` → Instrumentos con cambios detectados

---

## 🔧 Troubleshooting

### Error: "No module named 'pandas'"
```bash
# Asegúrate de tener el entorno virtual activado
pip install -r requirements.txt
```

### Error: "File not found: data/raw/..."
```bash
# Verifica que los archivos raw existen
ls data/raw/

# Si faltan, colócalos en data/raw/
```

### Error en Parsing de CSV
- Verifica que los archivos usan `;` como delimitador
- Verifica la codificación (debe ser `latin-1` o `utf-8`)
- Revisa que no hay líneas malformadas en los CSVs

### Error: "Permission denied" (PowerShell)
```powershell
# Ajustar política de ejecución
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📚 Documentación Adicional

- **Arquitectura de módulos**: Ver [src/logic/README.md](src/logic/README.md)
- **Dashboard React**: Ver [dashboard-financiero/README.md](dashboard-financiero/README.md)

---

## 👥 Equipo y Contribución

Para contribuir al proyecto:
1. Crear una rama feature: `git checkout -b feature/nueva-funcionalidad`
2. Hacer commits descriptivos
3. Ejecutar tests antes de push
4. Crear Pull Request con descripción clara

---

## 📄 Licencia

*Desarrollado para el proceso de conciliación de allocations de inversión.*

**Última actualización**: Febrero 2026

## Exportaciones del pipeline

### Export Balanceados (`export_balanceados.csv`)

Archivo de exportación para instrumentos clasificados como balanceados.

| Columna           | Origen / Descripción                                                                 |
|-------------------|-------------------------------------------------------------------------------------|
| ID                | Identificador único del instrumento (`df_final['ID']`)                              |
| Instrumento       | Nombre del instrumento (`df_final['Nombre']`)                                       |
| Id_ti_valor       | Código del instrumento en allocations nuevas (`allocations_nuevas['instrument']`)   |
| Id_ti             | Tipo de identificador usado para el match: RIC, Isin o Cusip (`allocations_nuevas['tipo_id']`) |
| Fecha             | Fecha de actualización calculada (ver lógica abajo)                                  |
| Clasificacion     | Literal "SubMoneda" (indica el tipo de clasificación que se actualiza)               |
| Moneda Anterior   | Clasificación antigua de moneda (`df_final['moneda_antigua']`)                      |
| Estado            | Calculado según lógica (ver abajo)                                                  |
| pct_original      | Porcentaje original de la allocation (`df_final['pct_original']`)                   |
| [USD, CLP, ...]   | Porcentaje de cada moneda específica (pivot de allocations_nuevas en formato WIDE)  |

#### Lógica de la columna Estado (Balanceados)
- **Estado_1**: Balanceado → Balanceado
- **Estado_2**: Moneda → Balanceado
- **Estado_3**: Solo si SubMoneda (de df_instruments) es "unassigned"

#### Lógica de la columna Fecha (Balanceados)
- **"31-12-2019"**: Si SubMoneda es "unassigned"
- **Primer día del mes actual**: En caso contrario (ejemplo: "01-03-2026")

---

### Export No Balanceados (`export_no_balanceados.csv`)

Archivo de exportación para instrumentos clasificados con una moneda específica (no balanceados).

| Columna           | Origen / Descripción                                                                 |
|-------------------|-------------------------------------------------------------------------------------|
| ID                | Identificador único del instrumento (`df_final['ID']`)                              |
| Instrumento       | Nombre del instrumento (`df_final['Nombre']`)                                       |
| SubMoneda         | Nueva clasificación de moneda (`df_final['moneda_nueva']`)                          |
| Moneda Anterior   | Clasificación antigua de moneda (`df_final['moneda_antigua']`)                      |
| Estado            | Calculado según lógica (ver abajo)                                                  |
| Sobreescribir     | "Sí" si hay cambio, "No" si no hay cambio (`df_final['Cambio']`)                  |

#### Lógica de la columna Estado (No Balanceados)
- **Estado_1**: Moneda → Misma Moneda (ej: USD → USD)
- **Estado_2**: Balanceado → Moneda
- **Estado_3**: Moneda → Otra Moneda (ej: USD → EUR)

---

### Notas Importantes

- Los exports se generan en la carpeta `data/exports/`
- Están diseñados para cumplir con los requerimientos de formato y linaje de datos del proceso de validación y actualización de allocations
- El export balanceados usa formato **WIDE** (una columna por moneda)
- El export no balanceados es más simple, solo con las columnas fijas necesarias
- Ambos mantienen el linaje completo desde los datos raw hasta el export final

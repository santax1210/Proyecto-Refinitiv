import { useState } from 'react';
import FileUploader from '../components/FileUploader';
import { useApp } from '../context/AppContext';

const TEAL = '#299D91';
const BORDER = '#DDE3E6';
const CLASIFICACIONES = ['Moneda', 'Región', 'Industria'];

export default function InicioPage() {
    const [clasificacion, setClasificacion] = useState('');
    const [attached, setAttached] = useState([]);
    const [files, setFiles] = useState({});
    const [processing, setProcessing] = useState(false);
    const [error, setError] = useState(null);
    
    const { uploadAndProcess, processingState } = useApp();

    // Manejar archivos adjuntos desde FileUploader
    const handleAttach = (attachedFiles) => {
        setAttached(attachedFiles);
        
        // Mapear archivos a los nombres esperados por el backend
        // Este mapeo depende de cómo FileUploader maneja los archivos
        const fileMap = {};
        attachedFiles.forEach(file => {
            // Los archivos deben tener un nombre específico esperado por el backend
            const fileName = file.name.toLowerCase();
            if (fileName.includes('posiciones')) {
                fileMap.posiciones = file;
            } else if (fileName.includes('instruments')) {
                fileMap.instruments = file;
            } else if (fileName.includes('nuevas')) {
                fileMap.allocations_nuevas = file;
            } else if (fileName.includes('currency') || fileName.includes('antiguas')) {
                fileMap.allocations_antiguas = file;
            }
        });
        setFiles(fileMap);
    };

    // Procesar archivos
    const handleProcess = async () => {
        if (Object.keys(files).length === 0) {
            setError('Debes subir al menos un archivo');
            return;
        }

        setProcessing(true);
        setError(null);

        try {
            await uploadAndProcess(files);
            // Éxito - el estado se maneja en el context
        } catch (err) {
            console.error('Error completo:', err);
            const errorMsg = err.message || 'Error al procesar archivos';
            setError(errorMsg);
            console.log('Error mostrado al usuario:', errorMsg);
        } finally {
            setProcessing(false);
        }
    };

    return (
        <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            width: '100%', height: '100%', padding: '28px 32px',
        }}>
            {/* ── Card split-panel ── */}
            <div style={{
                display: 'grid', gridTemplateColumns: '260px 1fr',
                width: '100%', maxWidth: 820,
                backgroundColor: '#FFFFFF',
                borderRadius: 24,
                border: `1px solid ${BORDER}`,
                boxShadow: '0 8px 32px rgba(0,0,0,0.10)',
                overflow: 'hidden',
                minHeight: 460,
            }}>

                {/* ── Panel izquierdo (branding con gradiente) ── */}
                <div style={{
                    background: 'linear-gradient(160deg, #1e6e67 0%, #299D91 55%, #34bfb0 100%)',
                    display: 'flex', flexDirection: 'column',
                    justifyContent: 'space-between',
                    padding: '36px 28px',
                }}>
                    {/* Logo + título */}
                    <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 28 }}>
                            <div style={{ width: 36, height: 36, borderRadius: 10, backgroundColor: 'rgba(255,255,255,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                                </svg>
                            </div>
                            <span style={{ fontSize: 15, fontWeight: 800, color: '#FFFFFF', letterSpacing: '-0.3px' }}>
                                Refinitiv
                            </span>
                        </div>

                        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 800, color: '#FFFFFF', lineHeight: 1.25, letterSpacing: '-0.5px' }}>
                            Validación de Allocations
                        </h1>
                        <p style={{ margin: '12px 0 0', fontSize: 13, color: 'rgba(255,255,255,0.75)', lineHeight: 1.6 }}>
                            Cargá los archivos de allocations y ejecutá el proceso de validación automatizado.
                        </p>
                    </div>

                    {/* Stats decorativos */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                        {[
                            { label: 'Procesamiento', value: 'Automático' },
                            { label: 'Seguridad', value: 'Encriptado' },
                            { label: 'Reportes', value: 'Tiempo Real' },
                        ].map(item => (
                            <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', borderRadius: 10, backgroundColor: 'rgba(255,255,255,0.12)' }}>
                                <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.7)' }}>{item.label}</span>
                                <span style={{ fontSize: 11, fontWeight: 700, color: '#FFFFFF' }}>{item.value}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* ── Panel derecho (upload) ── */}
                <div style={{ display: 'flex', flexDirection: 'column', padding: '28px 28px', gap: 16 }}>

                    {/* Cabecera */}
                    <div>
                        <p style={{ margin: 0, fontSize: 9, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.12em', color: '#9F9F9F' }}>
                            Paso 1 de 2
                        </p>
                        <h2 style={{ margin: '4px 0 0', fontSize: 16, fontWeight: 700, color: '#191919' }}>
                            Subir Archivo
                        </h2>
                    </div>

                    {/* Clasificación con chips */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
                        <label style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#71717A' }}>
                            TIPO DE CLASIFICACION
                        </label>
                        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                            {CLASIFICACIONES.map(c => {
                                const active = clasificacion === c;
                                return (
                                    <button key={c} onClick={() => setClasificacion(active ? '' : c)}
                                        style={{
                                            padding: '5px 12px', borderRadius: 7,
                                            fontSize: 11, fontWeight: 600,
                                            border: `1px solid ${active ? TEAL : BORDER}`,
                                            backgroundColor: active ? '#EBF7F6' : '#FFFFFF',
                                            color: active ? TEAL : '#525256', cursor: 'pointer',
                                            transition: 'all 0.12s',
                                        }}
                                        onMouseEnter={e => { if (!active) { e.currentTarget.style.borderColor = TEAL; e.currentTarget.style.color = TEAL; } }}
                                        onMouseLeave={e => { if (!active) { e.currentTarget.style.borderColor = BORDER; e.currentTarget.style.color = '#525256'; } }}
                                    >
                                        {c}
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* Divisor */}
                    <div style={{ height: 1, backgroundColor: '#F0F2F4' }} />

                    {/* FileUploader */}
                    <div style={{ flex: 1 }}>
                        <FileUploader onAttach={handleAttach} />
                    </div>

                    {/* Estado de procesamiento */}
                    {processing && (
                        <div style={{
                            display: 'flex', flexDirection: 'column', gap: 8,
                            padding: '12px 16px', borderRadius: 12,
                            backgroundColor: processingState.status === 'error' ? '#FEE2E2' : '#F3F6F8',
                            border: `1px solid ${processingState.status === 'error' ? '#FCA5A5' : BORDER}`,
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                {processingState.status !== 'error' ? (
                                    <div style={{ 
                                        width: 16, height: 16, 
                                        border: '2px solid ' + TEAL, 
                                        borderTopColor: 'transparent',
                                        borderRadius: '50%',
                                        animation: 'spin 1s linear infinite'
                                    }} />
                                ) : (
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#991B1B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <circle cx="12" cy="12" r="10" />
                                        <line x1="15" y1="9" x2="9" y2="15" />
                                        <line x1="9" y1="9" x2="15" y2="15" />
                                    </svg>
                                )}
                                <p style={{ margin: 0, fontSize: 12, fontWeight: 600, color: processingState.status === 'error' ? '#991B1B' : '#525256' }}>
                                    {processingState.message || 'Procesando...'}
                                </p>
                            </div>
                            {processingState.progress > 0 && processingState.status !== 'error' && (
                                <div style={{ height: 4, borderRadius: 2, backgroundColor: '#E8EAED', overflow: 'hidden' }}>
                                    <div style={{ 
                                        height: '100%', 
                                        width: `${processingState.progress}%`, 
                                        backgroundColor: TEAL, 
                                        transition: 'width 0.3s' 
                                    }} />
                                </div>
                            )}
                            {processingState.error && (
                                <p style={{ margin: 0, fontSize: 11, color: '#991B1B', lineHeight: 1.4 }}>
                                    {processingState.error}
                                </p>
                            )}
                        </div>
                    )}

                    {/* Error */}
                    {error && (
                        <div style={{
                            padding: '12px 16px', borderRadius: 12,
                            backgroundColor: '#FEE2E2', border: '1px solid #FCA5A5',
                        }}>
                            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#991B1B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, marginTop: 2 }}>
                                    <circle cx="12" cy="12" r="10" />
                                    <line x1="12" y1="8" x2="12" y2="12" />
                                    <line x1="12" y1="16" x2="12.01" y2="16" />
                                </svg>
                                <div style={{ flex: 1 }}>
                                    <p style={{ margin: 0, fontSize: 12, fontWeight: 700, color: '#991B1B', marginBottom: 4 }}>
                                        Error al procesar
                                    </p>
                                    <p style={{ margin: 0, fontSize: 11, color: '#991B1B', lineHeight: 1.4, whiteSpace: 'pre-wrap' }}>
                                        {error}
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Banner de éxito */}
                    {attached.length > 0 && !processing && (
                        <div style={{
                            display: 'flex', alignItems: 'center', gap: 12,
                            padding: '12px 16px', borderRadius: 12,
                            backgroundColor: '#EBF7F6', border: `1px solid ${TEAL}`,
                        }}>
                            <div style={{ width: 24, height: 24, borderRadius: '50%', backgroundColor: TEAL, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                                    <polyline points="20 6 9 17 4 12" />
                                </svg>
                            </div>
                            <div style={{ flex: 1 }}>
                                <p style={{ margin: 0, fontSize: 12, fontWeight: 700, color: '#1a7a70' }}>
                                    {attached.length} archivo{attached.length > 1 ? 's' : ''} listo{attached.length > 1 ? 's' : ''}
                                </p>
                            </div>
                            <button
                                onClick={handleProcess}
                                disabled={processing}
                                style={{
                                    padding: '6px 14px',
                                    borderRadius: 8,
                                    border: 'none',
                                    backgroundColor: TEAL,
                                    color: '#FFFFFF',
                                    fontSize: 11,
                                    fontWeight: 700,
                                    cursor: processing ? 'not-allowed' : 'pointer',
                                    opacity: processing ? 0.6 : 1,
                                    transition: 'opacity 0.2s',
                                }}
                            >
                                Procesar
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

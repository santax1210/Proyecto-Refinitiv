import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom';
import App from './App.jsx'

/**
 * Escala la UI proporcionalmente al ancho del viewport.
 * Referencia de diseño: 1536px (viewport CSS típico de laptop 1920×1080 @ 125% DPI).
 * - En el laptop → scale = 1.0  (sin cambios)
 * - En monitor   → scale > 1.0  (todo se ve proporcionalmente más grande)
 * Nunca baja de 1.0 para no tocar la calibración original del laptop.
 */
function applyViewportScale() {
  const DESIGN_WIDTH = 1536;
  const scale = Math.min(Math.max(window.innerWidth / DESIGN_WIDTH, 1.0), 1.5);
  document.documentElement.style.zoom = String(scale);
}

applyViewportScale();
window.addEventListener('resize', applyViewportScale, { passive: true });

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)

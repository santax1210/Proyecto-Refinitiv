import { useState } from 'react';
import { login } from '../services/apiService';

/**
 * Página de inicio de sesión.
 * Llama a /api/login, guarda el token JWT en localStorage y notifica al padre.
 */
export default function LoginPage({ onLoginSuccess }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPass, setShowPass] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      onLoginSuccess();
    } catch (err) {
      setError(err.message || 'Error al iniciar sesión');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-root">
      {/* Fondo animado */}
      <div className="login-bg">
        <div className="login-blob blob-1" />
        <div className="login-blob blob-2" />
        <div className="login-blob blob-3" />
      </div>

      {/* Card */}
      <div className="login-card">
        {/* Logotipo / Icono */}
        <div className="login-logo-wrap">
          <div className="login-logo-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor"
              strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5Z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
        </div>

        <h1 className="login-title">Refinitiv Automation</h1>
        <p className="login-subtitle">Ingresa tus credenciales para continuar</p>

        <form onSubmit={handleSubmit} className="login-form">
          {/* Usuario */}
          <div className="login-field">
            <label htmlFor="login-username" className="login-label">Usuario</label>
            <div className="login-input-wrap">
              <span className="login-input-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="8" r="4" />
                  <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" />
                </svg>
              </span>
              <input
                id="login-username"
                type="text"
                className="login-input"
                placeholder="admin"
                value={username}
                onChange={e => setUsername(e.target.value)}
                autoComplete="username"
                required
              />
            </div>
          </div>

          {/* Contraseña */}
          <div className="login-field">
            <label htmlFor="login-password" className="login-label">Contraseña</label>
            <div className="login-input-wrap">
              <span className="login-input-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
              </span>
              <input
                id="login-password"
                type={showPass ? 'text' : 'password'}
                className="login-input"
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
              <button
                type="button"
                className="login-eye-btn"
                onClick={() => setShowPass(v => !v)}
                aria-label={showPass ? 'Ocultar contraseña' : 'Mostrar contraseña'}
              >
                {showPass ? (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                    strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                    <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </svg>
                ) : (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                    strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="login-error" role="alert">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              {error}
            </div>
          )}

          {/* Botón */}
          <button
            id="btn-login-submit"
            type="submit"
            className="login-btn"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="login-spinner" />
                Verificando...
              </>
            ) : (
              'Iniciar sesión'
            )}
          </button>
        </form>

        <p className="login-footer">
          Sistema interno de validación — Finantech
        </p>
      </div>

      <style>{`
        /* ── Root ── */
        .login-root {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #0f1117;
          position: relative;
          overflow: hidden;
          font-family: 'Inter', 'Segoe UI', sans-serif;
        }

        /* ── Blobs animados ── */
        .login-bg { position: absolute; inset: 0; pointer-events: none; }
        .login-blob {
          position: absolute;
          border-radius: 50%;
          filter: blur(80px);
          opacity: 0.25;
          animation: blobFloat 10s ease-in-out infinite alternate;
        }
        .blob-1 {
          width: 520px; height: 520px;
          background: radial-gradient(circle, #6366f1, #8b5cf6);
          top: -120px; left: -100px;
          animation-duration: 12s;
        }
        .blob-2 {
          width: 400px; height: 400px;
          background: radial-gradient(circle, #3b82f6, #06b6d4);
          bottom: -80px; right: -60px;
          animation-duration: 9s;
          animation-delay: -3s;
        }
        .blob-3 {
          width: 300px; height: 300px;
          background: radial-gradient(circle, #a855f7, #ec4899);
          top: 50%; left: 60%;
          animation-duration: 14s;
          animation-delay: -6s;
        }
        @keyframes blobFloat {
          0%   { transform: translate(0, 0) scale(1); }
          50%  { transform: translate(30px, -20px) scale(1.05); }
          100% { transform: translate(-20px, 30px) scale(0.97); }
        }

        /* ── Card ── */
        .login-card {
          position: relative;
          z-index: 10;
          width: 100%;
          max-width: 420px;
          margin: 24px;
          background: rgba(255,255,255,0.05);
          backdrop-filter: blur(24px);
          -webkit-backdrop-filter: blur(24px);
          border: 1px solid rgba(255,255,255,0.12);
          border-radius: 24px;
          padding: 44px 40px 36px;
          box-shadow: 0 32px 80px rgba(0,0,0,0.5), 0 0 0 1px rgba(99,102,241,0.1);
        }

        /* ── Logo ── */
        .login-logo-wrap {
          display: flex;
          justify-content: center;
          margin-bottom: 24px;
        }
        .login-logo-icon {
          width: 64px; height: 64px;
          background: linear-gradient(135deg, #6366f1, #8b5cf6);
          border-radius: 18px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #fff;
          box-shadow: 0 8px 32px rgba(99,102,241,0.45);
        }

        /* ── Texts ── */
        .login-title {
          text-align: center;
          font-size: 1.4rem;
          font-weight: 700;
          color: #f1f5f9;
          margin: 0 0 6px;
          letter-spacing: -0.3px;
        }
        .login-subtitle {
          text-align: center;
          font-size: 0.875rem;
          color: #94a3b8;
          margin: 0 0 32px;
        }

        /* ── Form ── */
        .login-form { display: flex; flex-direction: column; gap: 20px; }
        .login-field { display: flex; flex-direction: column; gap: 8px; }
        .login-label {
          font-size: 0.8rem;
          font-weight: 600;
          color: #cbd5e1;
          letter-spacing: 0.4px;
          text-transform: uppercase;
        }
        .login-input-wrap {
          position: relative;
          display: flex;
          align-items: center;
        }
        .login-input-icon {
          position: absolute;
          left: 14px;
          color: #64748b;
          display: flex;
          pointer-events: none;
        }
        .login-input {
          width: 100%;
          background: rgba(255,255,255,0.07);
          border: 1px solid rgba(255,255,255,0.12);
          border-radius: 12px;
          padding: 12px 44px 12px 42px;
          color: #f1f5f9;
          font-size: 0.9rem;
          outline: none;
          transition: border-color 0.2s, box-shadow 0.2s, background 0.2s;
          box-sizing: border-box;
        }
        .login-input::placeholder { color: #475569; }
        .login-input:focus {
          border-color: #6366f1;
          background: rgba(99,102,241,0.1);
          box-shadow: 0 0 0 3px rgba(99,102,241,0.2);
        }
        .login-eye-btn {
          position: absolute;
          right: 14px;
          background: none;
          border: none;
          cursor: pointer;
          color: #64748b;
          display: flex;
          padding: 2px;
          transition: color 0.15s;
        }
        .login-eye-btn:hover { color: #a5b4fc; }

        /* ── Error ── */
        .login-error {
          display: flex;
          align-items: center;
          gap: 8px;
          background: rgba(239,68,68,0.12);
          border: 1px solid rgba(239,68,68,0.3);
          border-radius: 10px;
          padding: 10px 14px;
          color: #fca5a5;
          font-size: 0.85rem;
          animation: fadeIn 0.2s ease;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }

        /* ── Botón ── */
        .login-btn {
          width: 100%;
          padding: 13px;
          background: linear-gradient(135deg, #6366f1, #8b5cf6);
          border: none;
          border-radius: 12px;
          color: #fff;
          font-size: 0.95rem;
          font-weight: 600;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          transition: opacity 0.2s, transform 0.15s, box-shadow 0.2s;
          box-shadow: 0 4px 20px rgba(99,102,241,0.4);
          margin-top: 4px;
        }
        .login-btn:hover:not(:disabled) {
          opacity: 0.92;
          transform: translateY(-1px);
          box-shadow: 0 6px 28px rgba(99,102,241,0.5);
        }
        .login-btn:active:not(:disabled) { transform: translateY(0); }
        .login-btn:disabled { opacity: 0.6; cursor: not-allowed; }

        /* ── Spinner ── */
        .login-spinner {
          width: 16px; height: 16px;
          border: 2px solid rgba(255,255,255,0.3);
          border-top-color: #fff;
          border-radius: 50%;
          animation: spin 0.7s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* ── Footer ── */
        .login-footer {
          text-align: center;
          font-size: 0.75rem;
          color: #475569;
          margin: 24px 0 0;
        }
      `}</style>
    </div>
  );
}

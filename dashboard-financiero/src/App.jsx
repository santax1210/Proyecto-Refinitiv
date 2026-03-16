import { useState } from 'react';
import './index.css';

import Sidebar from './components/Sidebar';
import { ToastProvider } from './context/ToastContext';

import GoalsSection from './components/GoalsSection';
import CategorySection from './components/CategorySection';
import InicioPage from './pages/InicioPage';
import ValidacionPage from './pages/ValidacionPage';
import VisualizacionPage from './pages/VisualizacionPage';
import LoginPage from './pages/LoginPage';
import { AppProvider } from './context/AppContext';
import { isAuthenticated, logout } from './services/apiService';

/* ── Página de placeholder para secciones aún no construidas ── */
function PlaceholderPage({ name }) {
  return (
    <div className="flex flex-col items-center justify-center flex-1 gap-4" style={{ color: '#9F9F9F' }}>
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
        strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <line x1="9" y1="9" x2="15" y2="9" /><line x1="9" y1="12" x2="13" y2="12" />
      </svg>
      <p className="text-lg font-semibold">{name}</p>
      <p className="text-sm">Esta sección está en construcción.</p>
    </div>
  );
}

/* ── Página de "Inicio original" (Goals + Category) ── */
function OverviewPage() {
  return (
    <div className="flex-1 overflow-y-auto px-8 py-6 flex flex-col gap-8" style={{ backgroundColor: '#FAFAFA' }}>
      <GoalsSection />
      <CategorySection />
    </div>
  );
}

/* ── Layout principal con centros y scroll único ── */
function MainContent({ activePage, onNavigate, selectedId, onSelect }) {
  const renderPage = () => {
    switch (activePage) {
      case 'inicio': return <InicioPage />;
      case 'validacion': return <ValidacionPage onNavigate={onNavigate} onSelect={onSelect} />;
      case 'visualizacion': return <VisualizacionPage selectedId={selectedId} onSelect={onSelect} />;
      case 'ajustes': return <PlaceholderPage name="Ajustes" />;
      default: return <InicioPage />;
    }
  };

  return (
    <main
      className="flex-1 overflow-y-auto"
      style={{ backgroundColor: '#F5F7FA' }}
    >
      <div key={activePage} className="page-transition w-full min-h-full flex flex-col items-center">
        {renderPage()}
      </div>
    </main>
  );
}

export default function App() {
  const [loggedIn, setLoggedIn] = useState(() => isAuthenticated());
  const [activePage, setActivePage] = useState('inicio');
  const [selectedInstrumentId, setSelectedInstrumentId] = useState(23);

  function handleLoginSuccess() {
    setLoggedIn(true);
  }

  function handleLogout() {
    logout();
    setLoggedIn(false);
  }

  if (!loggedIn) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <AppProvider>
      <ToastProvider>
        <div className="flex h-screen overflow-hidden">
          <Sidebar activePage={activePage} onNavigate={setActivePage} onLogout={handleLogout} />
          <MainContent
            activePage={activePage}
            onNavigate={setActivePage}
            selectedId={selectedInstrumentId}
            onSelect={setSelectedInstrumentId}
          />
        </div>
      </ToastProvider>
    </AppProvider>
  );
}


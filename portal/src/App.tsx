import { useEffect, useState } from "react";
import { Link, Navigate, NavLink, Route, Routes, useNavigate } from "react-router-dom";
import { identityApi } from "./api/clienteIdentidad";
import { Ingreso } from "./paginas/acceso/Ingreso";
import { Portada } from "./paginas/acceso/Portada";
import { Recuperar } from "./paginas/acceso/Recuperar";
import { Registro } from "./paginas/acceso/Registro";
import { SegundoPaso } from "./paginas/acceso/SegundoPaso";
import { AdminCatalogo } from "./paginas/admin/AdminCatalogo";
import { TableroAdmin } from "./paginas/admin/TableroAdmin";
import { AgendaNegocios } from "./paginas/agenda/AgendaNegocios";
import { MisEntradas } from "./paginas/entradas/MisEntradas";
import { ValidarQrPuerta } from "./paginas/entradas/ValidarQrPuerta";
import { ListaEventos } from "./paginas/eventos/ListaEventos";
import { PlanoStands } from "./paginas/eventos/PlanoStands";
import { Inicio } from "./paginas/inicio/Inicio";
import { MisFacturas } from "./paginas/pagos/MisFacturas";
import { PagarOrden } from "./paginas/pagos/PagarOrden";
import { MiCuenta } from "./paginas/perfil/MiCuenta";
import { MisReservas } from "./paginas/reservas/MisReservas";
import { MesaAyudaTickets } from "./paginas/soporte/MesaAyudaTickets";
import { MonitoreoDispositivos } from "./paginas/soporte/MonitoreoDispositivos";
import { ProtectedRoute, useSession } from "./sesion/almacenSesion";
import { suscribirMantenimiento } from "./api/mantenimiento";
import { Mantenimiento } from "./paginas/Mantenimiento";

export function App() {
  const { user, refreshToken, clearSession } = useSession();
  const navigate = useNavigate();
  // Tema: el elegido antes (si se guardó) o el del sistema
  const [darkTheme, setDarkTheme] = useState(() => {
    let saved: string | null = null;
    try {
      saved = localStorage.getItem("exponexo-tema");
    } catch {
      // Navegación privada sin almacenamiento: se usa el del sistema
    }
    return saved ? saved === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", darkTheme ? "dark" : "light");
  }, [darkTheme]);

  const [servicioCaido, setServicioCaido] = useState<string | null>(null);
  useEffect(() => suscribirMantenimiento(setServicioCaido), []);

  const toggleTheme = () => {
    const next = !darkTheme;
    setDarkTheme(next);
    try {
      localStorage.setItem("exponexo-tema", next ? "dark" : "light");
    } catch {
      // Sin almacenamiento: el cambio dura mientras la pestaña esté abierta
    }
  };

  const handleLogout = async () => {
    if (refreshToken) {
      try {
        await identityApi.logout(refreshToken);
      } catch {
        // Limpieza local en memoria
      }
    }
    clearSession();
    navigate("/ingreso");
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to={user ? "/inicio" : "/"} className="brand-title">
          <img src="/icono.svg" alt="" width="30" height="30" />
          <span>Ferias y eventos</span>
        </Link>

        <nav className="nav-links" aria-label="Navegación principal">
          <NavLink to="/eventos">Eventos</NavLink>
          {user && (
            <>
              <NavLink to="/inicio">Inicio</NavLink>
              {user.rol === "expositor" && <NavLink to="/reservas">Mis reservas</NavLink>}
              {(user.rol === "visitante" || user.rol === "expositor") && (
                <>
                  <NavLink to="/mis-entradas">Mis entradas</NavLink>
                  <NavLink to="/agenda">Agenda B2B</NavLink>
                  <NavLink to="/facturas">Facturas</NavLink>
                </>
              )}
              <NavLink to="/soporte/tickets">Mesa de ayuda</NavLink>
              {(user.rol === "personal" || user.rol === "administrador") && (
                <>
                  <NavLink to="/puerta/validar-qr">Validar QR</NavLink>
                  <NavLink to="/soporte/dispositivos">Dispositivos</NavLink>
                </>
              )}
              {user.rol === "administrador" && (
                <>
                  <NavLink to="/admin/tablero">Tablero</NavLink>
                  <NavLink to="/admin/catalogo">Catálogo</NavLink>
                </>
              )}
            </>
          )}
        </nav>

        <div className="topbar-acciones">
          <button
            type="button"
            className="boton-icono"
            onClick={toggleTheme}
            aria-label={darkTheme ? "Cambiar a tema claro" : "Cambiar a tema oscuro"}
            title={darkTheme ? "Tema claro" : "Tema oscuro"}
          >
            {darkTheme ? (
              <svg viewBox="0 0 24 24" width="19" height="19" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
                <circle cx="12" cy="12" r="4.2" />
                <path d="M12 2.5v2.2M12 19.3v2.2M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.6 19.4l1.6-1.6M17.8 6.2l1.6-1.6" />
              </svg>
            ) : (
              <svg viewBox="0 0 24 24" width="19" height="19" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20.5 14.2A8.5 8.5 0 0 1 9.8 3.5a8.5 8.5 0 1 0 10.7 10.7Z" />
              </svg>
            )}
          </button>
          {user ? (
            <>
              <Link to="/perfil" className="usuario-chip" title="Mi cuenta">
                <span className="usuario-avatar" aria-hidden="true">
                  {user.nombre.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0]?.toUpperCase()).join("")}
                </span>
                <span className="usuario-datos">
                  <strong>{user.nombre.split(/\s+/)[0]}</strong>
                  <small>{user.rol}</small>
                </span>
              </Link>
              <button type="button" className="boton-icono" onClick={handleLogout} aria-label="Cerrar sesión" title="Cerrar sesión">
                <svg viewBox="0 0 24 24" width="19" height="19" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3M10 17l5-5-5-5M15 12H4" />
                </svg>
              </button>
            </>
          ) : (
            <>
              <Link to="/ingreso" className="boton-topbar boton-topbar-suave">Ingresar</Link>
              <Link to="/registro" className="boton-topbar boton-topbar-lleno">Crear cuenta</Link>
            </>
          )}
        </div>
      </header>

      <main>
        {servicioCaido ? <Mantenimiento /> : (
        <Routes>
          <Route path="/" element={<Portada />} />
          <Route path="/registro" element={<Registro />} />
          <Route path="/ingreso" element={<Ingreso />} />
          <Route path="/segundo-paso" element={<SegundoPaso />} />
          <Route path="/recuperar" element={<Recuperar />} />
          <Route path="/eventos" element={<ListaEventos />} />
          <Route path="/eventos/:id/stands" element={<PlanoStands />} />
          <Route
            path="/inicio"
            element={
              <ProtectedRoute>
                <Inicio />
              </ProtectedRoute>
            }
          />
          <Route
            path="/reservas"
            element={
              <ProtectedRoute allowedRoles={["expositor"]}>
                <MisReservas />
              </ProtectedRoute>
            }
          />
          <Route
            path="/mis-entradas"
            element={
              <ProtectedRoute allowedRoles={["visitante", "expositor", "administrador"]}>
                <MisEntradas />
              </ProtectedRoute>
            }
          />
          <Route
            path="/puerta/validar-qr"
            element={
              <ProtectedRoute allowedRoles={["personal", "administrador"]}>
                <ValidarQrPuerta />
              </ProtectedRoute>
            }
          />
          <Route
            path="/agenda"
            element={
              <ProtectedRoute allowedRoles={["visitante", "expositor", "administrador"]}>
                <AgendaNegocios />
              </ProtectedRoute>
            }
          />
          <Route
            path="/pagar/:origen/:referencia"
            element={
              <ProtectedRoute allowedRoles={["expositor", "visitante"]}>
                <PagarOrden />
              </ProtectedRoute>
            }
          />
          <Route
            path="/facturas"
            element={
              <ProtectedRoute allowedRoles={["expositor", "visitante", "administrador"]}>
                <MisFacturas />
              </ProtectedRoute>
            }
          />
          <Route
            path="/soporte/tickets"
            element={
              <ProtectedRoute>
                <MesaAyudaTickets />
              </ProtectedRoute>
            }
          />
          <Route
            path="/soporte/dispositivos"
            element={
              <ProtectedRoute allowedRoles={["personal", "administrador"]}>
                <MonitoreoDispositivos />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/tablero"
            element={
              <ProtectedRoute allowedRoles={["administrador"]}>
                <TableroAdmin />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/catalogo"
            element={
              <ProtectedRoute allowedRoles={["administrador"]}>
                <AdminCatalogo />
              </ProtectedRoute>
            }
          />
          <Route
            path="/perfil"
            element={
              <ProtectedRoute>
                <MiCuenta />
              </ProtectedRoute>
            }
          />
          <Route path="/perfil/seguridad" element={<Navigate to="/perfil" replace />} />
        </Routes>
        )}
      </main>
      <footer className="pie-pagina">
        Plataforma de ferias y eventos — proyecto de portafolio de Luis Felipe Arias.
      </footer>
    </div>
  );
}

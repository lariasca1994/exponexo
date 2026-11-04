import { useEffect, useState } from "react";
import { Link, NavLink, Route, Routes, useNavigate } from "react-router-dom";
import { identityApi } from "./api/clienteIdentidad";
import { Ingreso } from "./paginas/acceso/Ingreso";
import { Portada } from "./paginas/acceso/Portada";
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
import { SeguridadPerfil } from "./paginas/perfil/SeguridadPerfil";
import { MisReservas } from "./paginas/reservas/MisReservas";
import { MesaAyudaTickets } from "./paginas/soporte/MesaAyudaTickets";
import { MonitoreoDispositivos } from "./paginas/soporte/MonitoreoDispositivos";
import { ProtectedRoute, useSession } from "./sesion/almacenSesion";

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
          <img src="/icono.svg" alt="ExpoNexo Logo" width="28" height="28" />
          <span>ExpoNexo</span>
        </Link>

        <nav className="nav-links">
          <NavLink to="/eventos">Eventos</NavLink>
          {user ? (
            <>
              <NavLink to="/inicio">Inicio</NavLink>
              {user.rol === "expositor" && <NavLink to="/reservas">Mis Reservas</NavLink>}
              {(user.rol === "visitante" || user.rol === "expositor") && (
                <>
                  <NavLink to="/mis-entradas">Mis Entradas</NavLink>
                  <NavLink to="/agenda">Agenda B2B</NavLink>
                  <NavLink to="/facturas">Facturas</NavLink>
                </>
              )}
              <NavLink to="/soporte/tickets">Mesa de Ayuda</NavLink>
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
              <NavLink to="/perfil/seguridad">Seguridad</NavLink>
              <span className="badge">
                {user.nombre} ({user.rol})
              </span>
              <button type="button" className="btn btn-secondary" onClick={handleLogout}>
                Salir
              </button>
            </>
          ) : (
            <>
              <NavLink to="/ingreso">Ingresar</NavLink>
              <NavLink to="/registro">Crear cuenta</NavLink>
            </>
          )}
          <button
            type="button"
            className="btn btn-secondary"
            onClick={toggleTheme}
            aria-label="Cambiar tema claro u oscuro"
          >
            {darkTheme ? "Tema claro" : "Tema oscuro"}
          </button>
        </nav>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<Portada />} />
          <Route path="/registro" element={<Registro />} />
          <Route path="/ingreso" element={<Ingreso />} />
          <Route path="/segundo-paso" element={<SegundoPaso />} />
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
            path="/perfil/seguridad"
            element={
              <ProtectedRoute>
                <SeguridadPerfil />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>
      <footer className="pie-pagina">
        ExpoNexo — proyecto de portafolio de Luis Felipe Arias.
      </footer>
    </div>
  );
}

import { useState } from "react";
import { Link, Route, Routes, useNavigate } from "react-router-dom";
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
  const [darkTheme, setDarkTheme] = useState(false);

  const toggleTheme = () => {
    const next = !darkTheme;
    setDarkTheme(next);
    document.documentElement.setAttribute("data-theme", next ? "dark" : "light");
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
          <Link to="/eventos">Eventos</Link>
          {user ? (
            <>
              <Link to="/inicio">Inicio</Link>
              {user.rol === "expositor" && <Link to="/reservas">Mis Reservas</Link>}
              {(user.rol === "visitante" || user.rol === "expositor") && (
                <>
                  <Link to="/mis-entradas">Mis Entradas</Link>
                  <Link to="/agenda">Agenda B2B</Link>
                  <Link to="/facturas">Facturas</Link>
                </>
              )}
              <Link to="/soporte/tickets">Mesa de Ayuda</Link>
              {(user.rol === "personal" || user.rol === "administrador") && (
                <>
                  <Link to="/puerta/validar-qr">Validar QR</Link>
                  <Link to="/soporte/dispositivos">Dispositivos</Link>
                </>
              )}
              {user.rol === "administrador" && (
                <>
                  <Link to="/admin/tablero">Tablero</Link>
                  <Link to="/admin/catalogo">Catálogo</Link>
                </>
              )}
              <Link to="/perfil/seguridad">Seguridad</Link>
              <span className="badge">
                {user.nombre} ({user.rol})
              </span>
              <button type="button" className="btn btn-secondary" onClick={handleLogout}>
                Salir
              </button>
            </>
          ) : (
            <>
              <Link to="/ingreso">Ingresar</Link>
              <Link to="/registro">Crear cuenta</Link>
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

      <main style={{ flex: 1 }}>
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
    </div>
  );
}

import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { identityApi } from "../../api/clienteIdentidad";
import { CampoContrasena, contrasenaValida } from "../../componentes/CampoContrasena";
import { PanelMarca } from "../../componentes/PanelMarca";

export function Registro() {
  const navigate = useNavigate();
  const [paso, setPaso] = useState<1 | 2>(1);
  const [nombre, setNombre] = useState("");
  const [correo, setCorreo] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [rol, setRol] = useState<"visitante" | "expositor">("visitante");
  const [codigo, setCodigo] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  const registrar = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!contrasenaValida(contrasena)) {
      setError("La contraseña no cumple todas las reglas.");
      return;
    }
    setCargando(true);
    try {
      await identityApi.registerAccount({ correo, nombre, contrasena, rol });
      setPaso(2);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo completar el registro.");
    } finally {
      setCargando(false);
    }
  };

  const confirmar = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      await identityApi.confirmEmail({ correo, codigo: codigo.trim() });
      navigate("/ingreso", { replace: true, state: { aviso: "Correo confirmado. Ya puedes ingresar." } });
    } catch (err) {
      setError(err instanceof Error ? err.message : "El código no es válido.");
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="login-page">
      <section className="login-panel" aria-labelledby="registro-title">
        <div className="login-form-content">
          <p className="login-step">Crear cuenta <span aria-hidden="true">·</span> Paso {paso} de 2</p>
          <h1 id="registro-title">{paso === 1 ? "Únete a ExpoNexo" : "Confirma tu correo"}</h1>
          <p className="login-description">
            {paso === 1
              ? "Crea tu cuenta de visitante o expositor. La verificación en dos pasos queda activa desde el primer ingreso."
              : `Enviamos un código a ${correo}. Escríbelo para activar tu cuenta.`}
          </p>

          {error && <div className="alert alert-error" role="alert">{error}</div>}

          {paso === 1 ? (
            <form onSubmit={registrar}>
              <div className="form-group">
                <label htmlFor="nombre">Nombre completo</label>
                <input id="nombre" className="input-field" type="text" autoComplete="name" required minLength={2} maxLength={120}
                  autoFocus value={nombre} onChange={(e) => setNombre(e.target.value)} />
              </div>
              <div className="form-group">
                <label htmlFor="correo">Correo electrónico</label>
                <input id="correo" className="input-field" type="email" autoComplete="email" required maxLength={254}
                  placeholder="nombre@correo.com" value={correo} onChange={(e) => setCorreo(e.target.value)} />
              </div>
              <div className="form-group">
                <label htmlFor="rol">Tipo de participación</label>
                <select id="rol" className="select-field" value={rol} onChange={(e) => setRol(e.target.value as "visitante" | "expositor")}>
                  <option value="visitante">Visitante (entradas y agenda de citas)</option>
                  <option value="expositor">Expositor (reserva de stands y citas)</option>
                </select>
              </div>
              <CampoContrasena id="contrasena" etiqueta="Contraseña" valor={contrasena} alCambiar={setContrasena} autoComplete="new-password" conMedidor />
              <button type="submit" className="btn btn-primary login-submit" disabled={cargando}>
                {cargando ? "Registrando…" : "Registrarme"}
              </button>
            </form>
          ) : (
            <form onSubmit={confirmar}>
              <div className="form-group">
                <label htmlFor="codigo">Código de confirmación</label>
                <input id="codigo" className="input-field input-codigo" type="text" inputMode="numeric" autoComplete="one-time-code"
                  maxLength={12} autoFocus required placeholder="123456" value={codigo} onChange={(e) => setCodigo(e.target.value)} />
              </div>
              <button type="submit" className="btn btn-primary login-submit" disabled={cargando}>
                {cargando ? "Confirmando…" : "Confirmar correo"}
              </button>
            </form>
          )}

          <p className="login-register">
            ¿Ya tienes cuenta? <Link to="/ingreso">Ingresa aquí</Link>
          </p>
        </div>
        <p className="login-panel-footer">Tus datos se usan solo para tu participación en las ferias.</p>
      </section>

      <PanelMarca eyebrow="Tu lugar en la feria" titulo="Reserva, visita y conecta." texto="Elige tu stand en el plano, compra tu entrada con QR y agenda citas de negocios sin cruces." />
    </div>
  );
}

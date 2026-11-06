import React, { useEffect, useState } from "react";
import { identityApi } from "../../api/clienteIdentidad";
import { CampoContrasena, contrasenaValida } from "../../componentes/CampoContrasena";
import { crearLlave, llavesDisponibles } from "../../sesion/llavesAcceso";
import type { SecurityProfileResponse, TotpSetupResponse } from "../../tipos/identidad";

const ROLES: Record<string, string> = {
  visitante: "Visitante",
  expositor: "Expositor",
  personal: "Personal del recinto",
  administrador: "Administrador"
};

function iniciales(nombre: string): string {
  return nombre.split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0]?.toUpperCase()).join("") || "?";
}

// Navegador y sistema a partir del agente de usuario, para reconocer cada sesión
function dispositivo(agente: string | null): string {
  if (!agente) return "Dispositivo";
  const navegador = /Edg\//.test(agente) ? "Edge" : /OPR\//.test(agente) ? "Opera" : /Firefox\//.test(agente) ? "Firefox"
    : /Chrome\//.test(agente) ? "Chrome" : /Safari\//.test(agente) ? "Safari" : "Navegador";
  const sistema = /Android/.test(agente) ? "Android" : /iPhone|iPad/.test(agente) ? "iOS" : /Windows/.test(agente) ? "Windows"
    : /Mac OS X/.test(agente) ? "macOS" : /Linux/.test(agente) ? "Linux" : "";
  return sistema ? `${navegador} en ${sistema}` : navegador;
}

function fecha(valor: string): string {
  return new Date(valor).toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" });
}

type Aviso = { tipo: "exito" | "error"; texto: string } | null;

export function MiCuenta() {
  const [perfil, setPerfil] = useState<SecurityProfileResponse | null>(null);
  const [aviso, setAviso] = useState<Aviso>(null);
  const [cargando, setCargando] = useState(true);

  // Contraseña
  const [actual, setActual] = useState("");
  const [nueva, setNueva] = useState("");
  const [confirmar, setConfirmar] = useState("");
  const [guardandoClave, setGuardandoClave] = useState(false);

  // App autenticadora, Telegram, respaldo y llaves
  const [totp, setTotp] = useState<TotpSetupResponse | null>(null);
  const [codigoTotp, setCodigoTotp] = useState("");
  const [enlaceTelegram, setEnlaceTelegram] = useState<string | null>(null);
  const [respaldo, setRespaldo] = useState<string[] | null>(null);
  const [nombreLlave, setNombreLlave] = useState("");

  const cargar = async () => {
    try {
      setPerfil(await identityApi.getSecurityProfile());
    } catch (err) {
      setAviso({ tipo: "error", texto: err instanceof Error ? err.message : "No se pudo cargar tu cuenta." });
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    void cargar();
  }, []);

  const ejecutar = async (accion: () => Promise<void>, exito?: string) => {
    setAviso(null);
    try {
      await accion();
      if (exito) setAviso({ tipo: "exito", texto: exito });
    } catch (err) {
      setAviso({ tipo: "error", texto: err instanceof Error ? err.message : "La operación no se pudo completar." });
    }
  };

  const cambiarClave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!contrasenaValida(nueva)) return setAviso({ tipo: "error", texto: "La nueva contraseña no cumple todas las reglas." });
    if (nueva !== confirmar) return setAviso({ tipo: "error", texto: "Las contraseñas nuevas no coinciden." });
    setGuardandoClave(true);
    await ejecutar(async () => {
      const res = await identityApi.changePassword({ contrasena_actual: actual, nueva_contrasena: nueva });
      setActual("");
      setNueva("");
      setConfirmar("");
      await cargar();
      setAviso({
        tipo: "exito",
        texto: `Contraseña actualizada. Se cerraron ${res.sesiones_cerradas} sesiones en otros dispositivos.`
      });
    });
    setGuardandoClave(false);
  };

  const vincularTelegram = () =>
    ejecutar(async () => {
      const { enlace } = await identityApi.startTelegramLink();
      setEnlaceTelegram(enlace);
      window.open(enlace, "_blank", "noopener");
    });

  const registrarLlave = (e: React.FormEvent) => {
    e.preventDefault();
    void ejecutar(async () => {
      const { opciones, desafio_token } = await identityApi.passkeyRegistrationOptions();
      const credencial = await crearLlave(opciones);
      await identityApi.registerPasskey({ nombre_dispositivo: nombreLlave.trim(), desafio_token, credencial });
      setNombreLlave("");
      await cargar();
    }, "Llave de acceso registrada.");
  };

  if (cargando && !perfil) {
    return (
      <div className="container">
        <div className="panel-card">Cargando tu cuenta…</div>
      </div>
    );
  }
  if (!perfil) {
    return (
      <div className="container">
        <div className="alert alert-error">{aviso?.texto ?? "No se pudo cargar tu cuenta."}</div>
      </div>
    );
  }

  const u = perfil.usuario;
  const app = perfil.metodos_mfa.find((m) => m.tipo === "app" && m.activo);
  const correoMfa = perfil.metodos_mfa.find((m) => m.tipo === "correo" && m.activo);
  const preferido = perfil.metodo_preferido === "app" ? "App autenticadora" : "Código por correo";

  return (
    <div className="container mi-cuenta">
      <h1>Mi cuenta</h1>
      <p>Tus datos, tus avisos y la seguridad de tu acceso.</p>

      {aviso && (
        <div className={`alert ${aviso.tipo === "exito" ? "alert-success" : "alert-error"}`} role={aviso.tipo === "error" ? "alert" : "status"}>
          {aviso.texto}
        </div>
      )}

      <div className="cuenta-grid">
        <section className="panel-card cuenta-tarjeta cuenta-identidad">
          <div className="cuenta-encabezado">
            <span className="avatar-grande" aria-hidden="true">{iniciales(u.nombre)}</span>
            <div>
              <h2>{u.nombre}</h2>
              <span className="chip-rol">{ROLES[u.rol] ?? u.rol}</span>
            </div>
          </div>
          <dl className="cuenta-datos">
            <div><dt>Correo</dt><dd>{u.correo}</dd></div>
            <div>
              <dt>Telegram</dt>
              <dd>{perfil.telegram_vinculado ? <span className="estado estado-ok">vinculado</span> : <span className="estado">sin vincular</span>}</dd>
            </div>
            <div>
              <dt>Verificación en dos pasos</dt>
              <dd><span className="estado estado-ok">activa</span> · {preferido}</dd>
            </div>
            <div><dt>Miembro desde</dt><dd>{fecha(u.creado_en)}</dd></div>
          </dl>
        </section>

        <section className="panel-card cuenta-tarjeta">
          <h2 className="cuenta-titulo">Cambiar contraseña</h2>
          <p className="cuenta-ayuda">Al cambiarla se cierran tus sesiones en otros dispositivos y recibes un aviso por correo y Telegram.</p>
          <form onSubmit={cambiarClave}>
            <CampoContrasena id="clave-actual" etiqueta="Contraseña actual" valor={actual} alCambiar={setActual} autoComplete="current-password" />
            <CampoContrasena id="clave-nueva" etiqueta="Nueva contraseña" valor={nueva} alCambiar={setNueva} autoComplete="new-password" conMedidor />
            <CampoContrasena id="clave-confirmar" etiqueta="Confirmar nueva contraseña" valor={confirmar} alCambiar={setConfirmar} autoComplete="new-password" />
            <div className="cuenta-acciones">
              <button type="submit" className="btn btn-primary" disabled={guardandoClave}>
                {guardandoClave ? "Guardando…" : "Guardar contraseña"}
              </button>
            </div>
          </form>
        </section>

        <section className="panel-card cuenta-tarjeta">
          <h2 className="cuenta-titulo">Avisos por Telegram</h2>
          <p className="cuenta-ayuda">
            Tus avisos de reservas, pagos, entradas, citas y soporte llegan a tu correo y, si lo vinculas, también a tu Telegram.
          </p>
          {perfil.telegram_vinculado ? (
            <div className="cuenta-acciones">
              <button type="button" className="btn btn-secondary" onClick={() => ejecutar(async () => setPerfil(await identityApi.unlinkTelegram()), "Telegram desvinculado.")}>
                Desvincular Telegram
              </button>
            </div>
          ) : enlaceTelegram ? (
            <div className="cuenta-pasos">
              <p>Se abrió el bot de avisos. Pulsa <strong>Iniciar</strong> en Telegram y luego vuelve aquí.</p>
              <div className="cuenta-acciones">
                <a className="btn btn-secondary" href={enlaceTelegram} target="_blank" rel="noopener noreferrer">Abrir Telegram otra vez</a>
                <button type="button" className="btn btn-primary" onClick={() => ejecutar(async () => { await cargar(); setEnlaceTelegram(null); })}>
                  Ya pulsé Iniciar
                </button>
              </div>
            </div>
          ) : (
            <div className="cuenta-acciones">
              <button type="button" className="btn btn-primary" onClick={vincularTelegram}>Vincular Telegram</button>
            </div>
          )}
        </section>

        <section className="panel-card cuenta-tarjeta">
          <h2 className="cuenta-titulo">App autenticadora</h2>
          <p className="cuenta-ayuda">
            {app
              ? "Activa. ¿Cambiaste de teléfono? Configúrala en el nuevo; la actual sigue funcionando hasta que confirmes."
              : "Usa Google Authenticator, Microsoft Authenticator o Authy para generar tus códigos sin depender del correo."}
          </p>
          {totp ? (
            <form className="cuenta-totp" onSubmit={(e) => {
              e.preventDefault();
              void ejecutar(async () => {
                setPerfil(await identityApi.confirmTotpSetup(codigoTotp.trim()));
                setTotp(null);
                setCodigoTotp("");
              }, "App autenticadora activada y definida como método preferido.");
            }}>
              <img src={totp.qr_datos_url} alt="Código QR para la app autenticadora" className="qr-preview" />
              <p className="cuenta-ayuda">Clave manual: <code>{totp.secreto}</code></p>
              <div className="form-group">
                <label htmlFor="codigo-totp">Primer código de 6 dígitos</label>
                <input id="codigo-totp" className="input-field input-codigo" inputMode="numeric" autoComplete="one-time-code"
                  maxLength={6} required value={codigoTotp} onChange={(e) => setCodigoTotp(e.target.value)} placeholder="123456" />
              </div>
              <div className="cuenta-acciones">
                <button type="button" className="btn btn-secondary" onClick={() => setTotp(null)}>Cancelar</button>
                <button type="submit" className="btn btn-primary">Activar app</button>
              </div>
            </form>
          ) : (
            <div className="cuenta-acciones">
              {app && perfil.metodo_preferido !== "app" && (
                <button type="button" className="btn btn-secondary" onClick={() => ejecutar(async () => setPerfil(await identityApi.setPreferredMfa("app")), "La app autenticadora es tu método por defecto.")}>
                  Usar por defecto
                </button>
              )}
              <button type="button" className={app ? "btn btn-secondary" : "btn btn-primary"} onClick={() => ejecutar(async () => setTotp(await identityApi.startTotpSetup()))}>
                {app ? "Configurar en otro teléfono" : "Configurar app"}
              </button>
            </div>
          )}
        </section>

        <section className="panel-card cuenta-tarjeta">
          <h2 className="cuenta-titulo">Código por correo y respaldo</h2>
          <p className="cuenta-ayuda">
            Código por correo: {correoMfa ? "activo" : "inactivo"}. Códigos de respaldo disponibles: <strong>{perfil.codigos_respaldo_disponibles}</strong>.
            Úsalos si pierdes el acceso a tu app y a tu correo.
          </p>
          {respaldo && (
            <div className="alert alert-warning">
              <div>
                <strong>Guárdalos en un lugar seguro; solo se muestran esta vez.</strong>
                <div className="codigos-respaldo">{respaldo.map((c) => <code key={c}>{c}</code>)}</div>
              </div>
            </div>
          )}
          <div className="cuenta-acciones">
            {!correoMfa && (
              <button type="button" className="btn btn-secondary" onClick={() => ejecutar(async () => setPerfil(await identityApi.enableEmailMfa()), "Código por correo activado.")}>
                Activar código por correo
              </button>
            )}
            {correoMfa && perfil.metodo_preferido !== "correo" && (
              <button type="button" className="btn btn-secondary" onClick={() => ejecutar(async () => setPerfil(await identityApi.setPreferredMfa("correo")), "El código por correo es tu método por defecto.")}>
                Usar correo por defecto
              </button>
            )}
            <button type="button" className="btn btn-secondary" onClick={() => ejecutar(async () => {
              setRespaldo((await identityApi.generateBackupCodes()).codigos);
              await cargar();
            })}>
              Generar códigos de respaldo
            </button>
          </div>
        </section>

        <section className="panel-card cuenta-tarjeta">
          <h2 className="cuenta-titulo">Llaves de acceso</h2>
          <p className="cuenta-ayuda">Ingresa con la huella, el rostro o el PIN de tu dispositivo, sin escribir la contraseña.</p>
          {perfil.llaves_acceso.length > 0 && (
            <ul className="cuenta-lista">
              {perfil.llaves_acceso.map((l) => (
                <li key={l.id}>
                  <strong>{l.nombre_dispositivo}</strong>
                  <span>{l.ultimo_uso_en ? `Último uso: ${fecha(l.ultimo_uso_en)}` : `Registrada: ${fecha(l.creada_en)}`}</span>
                </li>
              ))}
            </ul>
          )}
          {llavesDisponibles() ? (
            <form className="cuenta-llave" onSubmit={registrarLlave}>
              <input className="input-field" aria-label="Nombre del dispositivo" required minLength={2} maxLength={60}
                placeholder="Ej.: Portátil del trabajo" value={nombreLlave} onChange={(e) => setNombreLlave(e.target.value)} />
              <button type="submit" className="btn btn-secondary">Registrar llave</button>
            </form>
          ) : (
            <p className="cuenta-ayuda">Este navegador no admite llaves de acceso.</p>
          )}
        </section>

        <section className="panel-card cuenta-tarjeta">
          <h2 className="cuenta-titulo">Sesiones activas</h2>
          <ul className="cuenta-lista">
            {perfil.sesiones_activas.map((s) => (
              <li key={s.id}>
                <strong>{dispositivo(s.agente)}</strong>
                <span>Desde {fecha(s.creada_en)}</span>
              </li>
            ))}
          </ul>
          <p className="cuenta-ayuda">Cambiar la contraseña cierra todas las demás.</p>
        </section>
      </div>
    </div>
  );
}

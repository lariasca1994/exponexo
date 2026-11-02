import React, { useEffect, useState } from "react";
import { identityApi } from "../../api/clienteIdentidad";
import type { PavilionItem } from "../../tipos/identidad";

export function AdminCatalogo() {
  const [pabellones, setPabellones] = useState<PavilionItem[]>([]);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Event form
  const [evNombre, setEvNombre] = useState("");
  const [evSlug, setEvSlug] = useState("");
  const [evDesc, setEvDesc] = useState("");
  const [evInicio, setEvInicio] = useState("2027-06-10T13:00:00Z");
  const [evFin, setEvFin] = useState("2027-06-14T22:00:00Z");
  const [evPrecio, setEvPrecio] = useState("45000.00");
  const [evAforo, setEvAforo] = useState(3000);

  // Pavilion form
  const [pabNombre, setPabNombre] = useState("");
  const [pabCapacidad, setPabCapacidad] = useState(25);

  // Stand form
  const [stPabellonId, setStPabellonId] = useState("");
  const [stCodigo, setStCodigo] = useState("");
  const [stMetros, setStMetros] = useState("18.00");
  const [stTipo, setStTipo] = useState<"basico" | "esquinero" | "isla">("basico");
  const [stPrecio, setStPrecio] = useState("3500000.00");
  const [stFila, setStFila] = useState(1);
  const [stColumna, setStColumna] = useState(1);

  const cargarPabellones = async () => {
    try {
      const data = await identityApi.listPavilions();
      setPabellones(data);
      if (data.length > 0 && !stPabellonId) {
        setStPabellonId(data[0].id);
      }
    } catch {
      // Ignore initial load error
    }
  };

  useEffect(() => {
    void cargarPabellones();
  }, []);

  const handleCrearEvento = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMensaje(null);
    try {
      await identityApi.adminCreateEvent({
        nombre: evNombre,
        slug: evSlug,
        descripcion: evDesc,
        inicio: evInicio,
        fin: evFin,
        estado: "publicado",
        precio_entrada: evPrecio,
        aforo: evAforo
      });
      setMensaje(`Evento "${evNombre}" creado y publicado.`);
      setEvNombre("");
      setEvSlug("");
      setEvDesc("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al crear evento.");
    }
  };

  const handleCrearPabellon = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMensaje(null);
    try {
      const creado = await identityApi.adminCreatePavilion({
        nombre: pabNombre,
        capacidad_stands: pabCapacidad
      });
      setMensaje(`Pabellón "${creado.nombre}" creado.`);
      setPabNombre("");
      await cargarPabellones();
      setStPabellonId(creado.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al crear pabellón.");
    }
  };

  const handleCrearStand = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMensaje(null);
    try {
      await identityApi.adminCreateStand({
        pabellon_id: stPabellonId,
        codigo: stCodigo,
        metros_cuadrados: stMetros,
        tipo: stTipo,
        precio_base: stPrecio,
        fila: stFila,
        columna: stColumna
      });
      setMensaje(`Stand "${stCodigo.toUpperCase()}" agregado al pabellón.`);
      setStCodigo("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al crear stand.");
    }
  };

  return (
    <div className="container">
      <h1 style={{ marginTop: 0 }}>Administración del Catálogo</h1>

      {error && <div className="alert alert-error">{error}</div>}
      {mensaje && <div className="alert alert-success">{mensaje}</div>}

      <div className="grid-2">
        <div className="panel-card">
          <h3 style={{ marginTop: 0 }}>1. Crear Evento</h3>
          <form onSubmit={handleCrearEvento}>
            <div className="form-group">
              <label htmlFor="ev-nombre">Nombre del evento</label>
              <input
                id="ev-nombre"
                className="input-field"
                required
                value={evNombre}
                onChange={(e) => setEvNombre(e.target.value)}
                placeholder="Feria de Tecnología 2027"
              />
            </div>
            <div className="form-group">
              <label htmlFor="ev-slug">Slug URL (minúsculas y guiones)</label>
              <input
                id="ev-slug"
                className="input-field"
                required
                value={evSlug}
                onChange={(e) => setEvSlug(e.target.value)}
                placeholder="feria-tecnologia-2027"
              />
            </div>
            <div className="form-group">
              <label htmlFor="ev-desc">Descripción</label>
              <input
                id="ev-desc"
                className="input-field"
                value={evDesc}
                onChange={(e) => setEvDesc(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="ev-inicio">Inicio (UTC ISO)</label>
              <input
                id="ev-inicio"
                className="input-field"
                required
                value={evInicio}
                onChange={(e) => setEvInicio(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="ev-fin">Fin (UTC ISO)</label>
              <input
                id="ev-fin"
                className="input-field"
                required
                value={evFin}
                onChange={(e) => setEvFin(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="ev-precio">Precio entrada (COP)</label>
              <input
                id="ev-precio"
                className="input-field"
                required
                value={evPrecio}
                onChange={(e) => setEvPrecio(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="ev-aforo">Aforo máximo</label>
              <input
                id="ev-aforo"
                type="number"
                className="input-field"
                required
                value={evAforo}
                onChange={(e) => setEvAforo(Number(e.target.value))}
              />
            </div>
            <button type="submit" className="btn btn-primary">
              Publicar evento
            </button>
          </form>
        </div>

        <div>
          <div className="panel-card" style={{ marginBottom: "1.25rem" }}>
            <h3 style={{ marginTop: 0 }}>2. Crear Pabellón</h3>
            <form onSubmit={handleCrearPabellon}>
              <div className="form-group">
                <label htmlFor="pab-nombre">Nombre del pabellón</label>
                <input
                  id="pab-nombre"
                  className="input-field"
                  required
                  value={pabNombre}
                  onChange={(e) => setPabNombre(e.target.value)}
                  placeholder="Pabellón 3"
                />
              </div>
              <div className="form-group">
                <label htmlFor="pab-cap">Capacidad de stands</label>
                <input
                  id="pab-cap"
                  type="number"
                  className="input-field"
                  required
                  value={pabCapacidad}
                  onChange={(e) => setPabCapacidad(Number(e.target.value))}
                />
              </div>
              <button type="submit" className="btn btn-primary">
                Crear pabellón
              </button>
            </form>
          </div>

          <div className="panel-card">
            <h3 style={{ marginTop: 0 }}>3. Agregar Stand a un Pabellón</h3>
            <form onSubmit={handleCrearStand}>
              <div className="form-group">
                <label htmlFor="st-pab">Pabellón</label>
                <select
                  id="st-pab"
                  className="select-field"
                  required
                  value={stPabellonId}
                  onChange={(e) => setStPabellonId(e.target.value)}
                >
                  <option value="">Selecciona un pabellón</option>
                  {pabellones.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.nombre}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="st-cod">Código del stand</label>
                <input
                  id="st-cod"
                  className="input-field"
                  required
                  value={stCodigo}
                  onChange={(e) => setStCodigo(e.target.value)}
                  placeholder="P3-A12"
                />
              </div>
              <div className="form-group">
                <label htmlFor="st-tipo">Tipo</label>
                <select
                  id="st-tipo"
                  className="select-field"
                  value={stTipo}
                  onChange={(e) => setStTipo(e.target.value as "basico" | "esquinero" | "isla")}
                >
                  <option value="basico">Básico</option>
                  <option value="esquinero">Esquinero</option>
                  <option value="isla">Isla</option>
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="st-metros">Metros cuadrados</label>
                <input
                  id="st-metros"
                  className="input-field"
                  required
                  value={stMetros}
                  onChange={(e) => setStMetros(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label htmlFor="st-precio">Precio base (COP)</label>
                <input
                  id="st-precio"
                  className="input-field"
                  required
                  value={stPrecio}
                  onChange={(e) => setStPrecio(e.target.value)}
                />
              </div>
              <div className="grid-2">
                <div className="form-group">
                  <label htmlFor="st-fila">Fila</label>
                  <input
                    id="st-fila"
                    type="number"
                    className="input-field"
                    required
                    value={stFila}
                    onChange={(e) => setStFila(Number(e.target.value))}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="st-col">Columna</label>
                  <input
                    id="st-col"
                    type="number"
                    className="input-field"
                    required
                    value={stColumna}
                    onChange={(e) => setStColumna(Number(e.target.value))}
                  />
                </div>
              </div>
              <button type="submit" className="btn btn-primary">
                Crear stand
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

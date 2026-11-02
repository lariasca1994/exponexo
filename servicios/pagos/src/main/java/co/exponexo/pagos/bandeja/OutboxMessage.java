package co.exponexo.pagos.bandeja;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Lob;
import jakarta.persistence.Table;
import java.time.OffsetDateTime;

@Entity
@Table(name = "bandeja_salida")
public class OutboxMessage {

    @Id
    @Column(name = "id", length = 36, nullable = false)
    private String id;

    @Column(name = "tipo", length = 60, nullable = false)
    private String tipo;

    @Lob
    @Column(name = "carga", nullable = false)
    private String carga;

    @Column(name = "correlacion_id", length = 64)
    private String correlacionId;

    @Column(name = "creado_en", nullable = false)
    private OffsetDateTime creadoEn;

    @Column(name = "publicado_en")
    private OffsetDateTime publicadoEn;

    @Column(name = "intentos", nullable = false)
    private int intentos;

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getTipo() { return tipo; }
    public void setTipo(String tipo) { this.tipo = tipo; }
    public String getCarga() { return carga; }
    public void setCarga(String carga) { this.carga = carga; }
    public String getCorrelacionId() { return correlacionId; }
    public void setCorrelacionId(String correlacionId) { this.correlacionId = correlacionId; }
    public OffsetDateTime getCreadoEn() { return creadoEn; }
    public void setCreadoEn(OffsetDateTime creadoEn) { this.creadoEn = creadoEn; }
    public OffsetDateTime getPublicadoEn() { return publicadoEn; }
    public void setPublicadoEn(OffsetDateTime publicadoEn) { this.publicadoEn = publicadoEn; }
    public int getIntentos() { return intentos; }
    public void setIntentos(int intentos) { this.intentos = intentos; }
}

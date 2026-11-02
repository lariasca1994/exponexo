package co.exponexo.pagos.qr;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.OffsetDateTime;

@Entity
@Table(name = "cobros_qr")
public class QrCharge {

    @Id
    @Column(name = "id", length = 36, nullable = false)
    private String id;

    @Column(name = "orden_id", length = 36, nullable = false)
    private String ordenId;

    @Column(name = "contenido_huella", length = 128, nullable = false)
    private String contenidoHuella;

    @Column(name = "vence_en", nullable = false)
    private OffsetDateTime venceEn;

    @Column(name = "estado", length = 20, nullable = false)
    private String estado;

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getOrdenId() { return ordenId; }
    public void setOrdenId(String ordenId) { this.ordenId = ordenId; }
    public String getContenidoHuella() { return contenidoHuella; }
    public void setContenidoHuella(String contenidoHuella) { this.contenidoHuella = contenidoHuella; }
    public OffsetDateTime getVenceEn() { return venceEn; }
    public void setVenceEn(OffsetDateTime venceEn) { this.venceEn = venceEn; }
    public String getEstado() { return estado; }
    public void setEstado(String estado) { this.estado = estado; }
}

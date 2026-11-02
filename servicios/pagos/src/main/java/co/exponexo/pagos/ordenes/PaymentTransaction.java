package co.exponexo.pagos.ordenes;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.OffsetDateTime;

@Entity
@Table(name = "transacciones")
public class PaymentTransaction {

    @Id
    @Column(name = "id", length = 36, nullable = false)
    private String id;

    @Column(name = "orden_id", length = 36, nullable = false)
    private String ordenId;

    @Column(name = "metodo", length = 20, nullable = false)
    private String metodo;

    @Column(name = "estado", length = 20, nullable = false)
    private String estado;

    @Column(name = "codigo_autorizacion", length = 40)
    private String codigoAutorizacion;

    @Column(name = "ocurrida_en", nullable = false)
    private OffsetDateTime ocurridaEn;

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getOrdenId() { return ordenId; }
    public void setOrdenId(String ordenId) { this.ordenId = ordenId; }
    public String getMetodo() { return metodo; }
    public void setMetodo(String metodo) { this.metodo = metodo; }
    public String getEstado() { return estado; }
    public void setEstado(String estado) { this.estado = estado; }
    public String getCodigoAutorizacion() { return codigoAutorizacion; }
    public void setCodigoAutorizacion(String codigoAutorizacion) { this.codigoAutorizacion = codigoAutorizacion; }
    public OffsetDateTime getOcurridaEn() { return ocurridaEn; }
    public void setOcurridaEn(OffsetDateTime ocurridaEn) { this.ocurridaEn = ocurridaEn; }
}

-- Paquete PL/SQL para Oracle Autonomous Database (migración repetible R__)
CREATE OR REPLACE PACKAGE pkg_facturacion AS
    PROCEDURE emitir_factura(
        p_orden_id       IN  VARCHAR2,
        p_factura_id     IN  VARCHAR2,
        p_detalle_id     IN  VARCHAR2,
        p_prefijo        IN  VARCHAR2,
        p_nit_cliente    IN  VARCHAR2,
        p_razon_social   IN  VARCHAR2,
        p_descripcion    IN  VARCHAR2,
        p_porcentaje_iva IN  NUMBER,
        p_evento_id      IN  VARCHAR2,
        p_correlacion_id IN  VARCHAR2,
        p_numero_factura OUT VARCHAR2
    );

    PROCEDURE registrar_reembolso(
        p_orden_id       IN  VARCHAR2,
        p_reembolso_id   IN  VARCHAR2,
        p_monto          IN  NUMBER,
        p_motivo         IN  VARCHAR2,
        p_evento_id      IN  VARCHAR2,
        p_correlacion_id IN  VARCHAR2
    );
END pkg_facturacion;
/

CREATE OR REPLACE PACKAGE BODY pkg_facturacion AS
    PROCEDURE emitir_factura(
        p_orden_id       IN  VARCHAR2,
        p_factura_id     IN  VARCHAR2,
        p_detalle_id     IN  VARCHAR2,
        p_prefijo        IN  VARCHAR2,
        p_nit_cliente    IN  VARCHAR2,
        p_razon_social   IN  VARCHAR2,
        p_descripcion    IN  VARCHAR2,
        p_porcentaje_iva IN  NUMBER,
        p_evento_id      IN  VARCHAR2,
        p_correlacion_id IN  VARCHAR2,
        p_numero_factura OUT VARCHAR2
    ) IS
        v_monto      NUMBER(12, 2);
        v_estado     VARCHAR2(20);
        v_referencia VARCHAR2(64);
        v_origen     VARCHAR2(20);
        v_seq        NUMBER;
        v_subtotal   NUMBER(12, 2);
        v_impuesto   NUMBER(12, 2);
        v_ahora      TIMESTAMP WITH TIME ZONE := SYSTIMESTAMP;
        v_carga      CLOB;
    BEGIN
        SELECT monto, estado, referencia, origen
        INTO v_monto, v_estado, v_referencia, v_origen
        FROM ordenes_pago
        WHERE id = p_orden_id
        FOR UPDATE;

        IF v_estado = 'aprobada' THEN
            SELECT numero INTO p_numero_factura FROM facturas WHERE orden_id = p_orden_id;
            RETURN;
        END IF;

        IF v_estado NOT IN ('creada', 'pendiente') THEN
            RAISE_APPLICATION_ERROR(-20001, 'La orden no está en estado pagable.');
        END IF;

        v_seq := seq_numero_factura.NEXTVAL;
        p_numero_factura := p_prefijo || '-' || LPAD(TO_CHAR(v_seq), 6, '0');

        v_subtotal := ROUND(v_monto / (1 + (p_porcentaje_iva / 100)), 2);
        v_impuesto := v_monto - v_subtotal;

        UPDATE ordenes_pago
        SET estado = 'aprobada', actualizada_en = v_ahora
        WHERE id = p_orden_id;

        UPDATE cobros_qr
        SET estado = 'pagado'
        WHERE orden_id = p_orden_id AND estado = 'vigente';

        INSERT INTO facturas (
            id, orden_id, numero, fecha, nit_cliente, razon_social,
            subtotal, impuesto, total, estado
        ) VALUES (
            p_factura_id, p_orden_id, p_numero_factura, v_ahora, p_nit_cliente, p_razon_social,
            v_subtotal, v_impuesto, v_monto, 'emitida'
        );

        INSERT INTO detalle_factura (
            id, factura_id, descripcion, cantidad, valor_unitario, impuesto
        ) VALUES (
            p_detalle_id, p_factura_id, p_descripcion, 1, v_subtotal, v_impuesto
        );

        v_carga := '{"orden_id":"' || p_orden_id || '","referencia":"' || v_referencia ||
                   '","origen":"' || v_origen || '","monto":' || TO_CHAR(v_monto, 'FM9999999990.00') ||
                   ',"numero_factura":"' || p_numero_factura || '"}';

        INSERT INTO bandeja_salida (
            id, tipo, carga, correlacion_id, creado_en, publicado_en, intentos
        ) VALUES (
            p_evento_id, 'pago.aprobado', v_carga, p_correlacion_id, v_ahora, NULL, 0
        );
    END emitir_factura;

    PROCEDURE registrar_reembolso(
        p_orden_id       IN  VARCHAR2,
        p_reembolso_id   IN  VARCHAR2,
        p_monto          IN  NUMBER,
        p_motivo         IN  VARCHAR2,
        p_evento_id      IN  VARCHAR2,
        p_correlacion_id IN  VARCHAR2
    ) IS
        v_monto_orden NUMBER(12, 2);
        v_estado      VARCHAR2(20);
        v_referencia  VARCHAR2(64);
        v_origen      VARCHAR2(20);
        v_ahora       TIMESTAMP WITH TIME ZONE := SYSTIMESTAMP;
        v_carga       CLOB;
    BEGIN
        SELECT monto, estado, referencia, origen
        INTO v_monto_orden, v_estado, v_referencia, v_origen
        FROM ordenes_pago
        WHERE id = p_orden_id
        FOR UPDATE;

        IF v_estado <> 'aprobada' THEN
            RAISE_APPLICATION_ERROR(-20002, 'Solo se pueden reembolsar órdenes aprobadas.');
        END IF;

        IF p_monto <= 0 OR p_monto > v_monto_orden THEN
            RAISE_APPLICATION_ERROR(-20003, 'El monto del reembolso supera el valor pagado.');
        END IF;

        INSERT INTO reembolsos (id, orden_id, monto, motivo, estado, creado_en)
        VALUES (p_reembolso_id, p_orden_id, p_monto, p_motivo, 'aprobado', v_ahora);

        UPDATE ordenes_pago
        SET estado = 'reembolsada', actualizada_en = v_ahora
        WHERE id = p_orden_id;

        UPDATE facturas
        SET estado = 'anulada'
        WHERE orden_id = p_orden_id;

        v_carga := '{"orden_id":"' || p_orden_id || '","referencia":"' || v_referencia ||
                   '","origen":"' || v_origen || '","monto":' || TO_CHAR(p_monto, 'FM9999999990.00') || '}';

        INSERT INTO bandeja_salida (
            id, tipo, carga, correlacion_id, creado_en, publicado_en, intentos
        ) VALUES (
            p_evento_id, 'pago.reembolsado', v_carga, p_correlacion_id, v_ahora, NULL, 0
        );
    END registrar_reembolso;
END pkg_facturacion;
/

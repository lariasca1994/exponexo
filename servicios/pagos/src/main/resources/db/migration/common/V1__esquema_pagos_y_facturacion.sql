CREATE SEQUENCE seq_numero_factura START WITH 1 INCREMENT BY 1;

CREATE TABLE ordenes_pago (
    id VARCHAR(36) NOT NULL,
    referencia VARCHAR(64) NOT NULL,
    origen VARCHAR(20) NOT NULL,
    usuario_id VARCHAR(36) NOT NULL,
    monto DECIMAL(12, 2) NOT NULL,
    moneda VARCHAR(3) NOT NULL,
    estado VARCHAR(20) NOT NULL,
    clave_idempotencia VARCHAR(64) NOT NULL,
    creada_en TIMESTAMP WITH TIME ZONE NOT NULL,
    actualizada_en TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT pk_ordenes_pago PRIMARY KEY (id),
    CONSTRAINT uq_ordenes_idempotencia UNIQUE (clave_idempotencia),
    CONSTRAINT ck_ordenes_origen CHECK (origen IN ('stand', 'reserva_stand', 'entrada')),
    CONSTRAINT ck_ordenes_estado CHECK (estado IN ('creada', 'pendiente', 'aprobada', 'rechazada', 'expirada', 'reembolsada'))
);

CREATE INDEX ix_ordenes_pago_referencia ON ordenes_pago (referencia);
CREATE INDEX ix_ordenes_pago_usuario_id ON ordenes_pago (usuario_id);

CREATE TABLE transacciones (
    id VARCHAR(36) NOT NULL,
    orden_id VARCHAR(36) NOT NULL,
    metodo VARCHAR(20) NOT NULL,
    estado VARCHAR(20) NOT NULL,
    codigo_autorizacion VARCHAR(40),
    ocurrida_en TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT pk_transacciones PRIMARY KEY (id),
    CONSTRAINT fk_transacciones_orden FOREIGN KEY (orden_id) REFERENCES ordenes_pago (id),
    CONSTRAINT ck_transacciones_estado CHECK (estado IN ('iniciada', 'aprobada', 'rechazada'))
);

CREATE INDEX ix_transacciones_orden_id ON transacciones (orden_id);

CREATE TABLE cobros_qr (
    id VARCHAR(36) NOT NULL,
    orden_id VARCHAR(36) NOT NULL,
    contenido_huella VARCHAR(128) NOT NULL,
    vence_en TIMESTAMP WITH TIME ZONE NOT NULL,
    estado VARCHAR(20) NOT NULL,
    CONSTRAINT pk_cobros_qr PRIMARY KEY (id),
    CONSTRAINT fk_cobros_qr_orden FOREIGN KEY (orden_id) REFERENCES ordenes_pago (id),
    CONSTRAINT ck_cobros_qr_estado CHECK (estado IN ('vigente', 'pagado', 'vencido'))
);

CREATE INDEX ix_cobros_qr_orden_id ON cobros_qr (orden_id);

CREATE TABLE facturas (
    id VARCHAR(36) NOT NULL,
    orden_id VARCHAR(36) NOT NULL,
    numero VARCHAR(20) NOT NULL,
    fecha TIMESTAMP WITH TIME ZONE NOT NULL,
    nit_cliente VARCHAR(30) NOT NULL,
    razon_social VARCHAR(150) NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL,
    impuesto DECIMAL(12, 2) NOT NULL,
    total DECIMAL(12, 2) NOT NULL,
    estado VARCHAR(20) NOT NULL,
    CONSTRAINT pk_facturas PRIMARY KEY (id),
    CONSTRAINT uq_facturas_orden UNIQUE (orden_id),
    CONSTRAINT uq_facturas_numero UNIQUE (numero),
    CONSTRAINT fk_facturas_orden FOREIGN KEY (orden_id) REFERENCES ordenes_pago (id),
    CONSTRAINT ck_facturas_estado CHECK (estado IN ('emitida', 'anulada'))
);

CREATE TABLE detalle_factura (
    id VARCHAR(36) NOT NULL,
    factura_id VARCHAR(36) NOT NULL,
    descripcion VARCHAR(200) NOT NULL,
    cantidad DECIMAL(10, 2) NOT NULL,
    valor_unitario DECIMAL(12, 2) NOT NULL,
    impuesto DECIMAL(12, 2) NOT NULL,
    CONSTRAINT pk_detalle_factura PRIMARY KEY (id),
    CONSTRAINT fk_detalle_factura_factura FOREIGN KEY (factura_id) REFERENCES facturas (id)
);

CREATE INDEX ix_detalle_factura_factura_id ON detalle_factura (factura_id);

CREATE TABLE reembolsos (
    id VARCHAR(36) NOT NULL,
    orden_id VARCHAR(36) NOT NULL,
    monto DECIMAL(12, 2) NOT NULL,
    motivo VARCHAR(200) NOT NULL,
    estado VARCHAR(20) NOT NULL,
    creado_en TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT pk_reembolsos PRIMARY KEY (id),
    CONSTRAINT fk_reembolsos_orden FOREIGN KEY (orden_id) REFERENCES ordenes_pago (id),
    CONSTRAINT ck_reembolsos_estado CHECK (estado IN ('solicitado', 'aprobado', 'rechazado'))
);

CREATE INDEX ix_reembolsos_orden_id ON reembolsos (orden_id);

CREATE TABLE bandeja_salida (
    id VARCHAR(36) NOT NULL,
    tipo VARCHAR(60) NOT NULL,
    carga CLOB NOT NULL,
    correlacion_id VARCHAR(64),
    creado_en TIMESTAMP WITH TIME ZONE NOT NULL,
    publicado_en TIMESTAMP WITH TIME ZONE,
    intentos INT NOT NULL,
    CONSTRAINT pk_bandeja_salida PRIMARY KEY (id)
);

CREATE TABLE eventos_procesados (
    evento_id VARCHAR(36) NOT NULL,
    procesado_en TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT pk_eventos_procesados PRIMARY KEY (evento_id)
);

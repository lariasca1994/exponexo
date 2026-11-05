-- Depuración quincenal de pagos (Oracle): eventos ya publicados y ya procesados con más de 15 días.
-- Nunca toca órdenes, transacciones, facturas ni reembolsos.
DELETE FROM bandeja_salida WHERE publicado_en IS NOT NULL AND publicado_en < SYSTIMESTAMP - INTERVAL '15' DAY;
DELETE FROM eventos_procesados WHERE procesado_en < SYSTIMESTAMP - INTERVAL '15' DAY;
DELETE FROM cobros_qr WHERE estado = 'vencido' AND vence_en < SYSTIMESTAMP - INTERVAL '15' DAY;
COMMIT;

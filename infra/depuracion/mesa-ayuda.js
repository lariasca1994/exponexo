// Depuración quincenal de mesa de ayuda (MongoDB): eventos ya publicados con más de 15 días y
// retención de 15 días en las lecturas de dispositivos (la colección las borra sola).
// Nunca toca tickets ni dispositivos.
const limite = new Date(Date.now() - 15 * 24 * 3600 * 1000);
const bandeja = db.bandeja_salida.deleteMany({ publicado_en: { $ne: null, $lt: limite } });
if (db.getCollectionNames().includes('lecturas_dispositivo')) {
  db.runCommand({ collMod: 'lecturas_dispositivo', expireAfterSeconds: 15 * 24 * 3600 });
}
printjson({ bandeja_salida_borrados: bandeja.deletedCount, retencion_lecturas_dias: 15 });

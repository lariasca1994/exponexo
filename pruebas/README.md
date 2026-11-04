# Pruebas transversales

Las pruebas de cada servicio están en su propia carpeta. Aquí se encuentra la prueba de
integración del ciclo principal entre Identidad, reservas, pagos y entradas:
`test_e2e_integration.py`.

Desde la raíz del repositorio, prepara primero las dependencias de Identidad y las de prueba:

```powershell
python -m pip install -r servicios/identidad-reservas/requirements.txt
python -m pip install pytest pytest-cov
python -m pytest pruebas/test_e2e_integration.py -v
```

El workflow `.github/workflows/e2e.yml` genera claves RSA temporales y ejecuta el recorrido con
SQLite en memoria. No valida SQL Server ni Oracle reales. Las cuentas y datos de prueba deben ser
inventados; nunca incluyas secretos reales.

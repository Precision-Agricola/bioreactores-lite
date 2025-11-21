## [v1.3.0] - 2025-10-30

### Added (Sensores)
- Implementación completa del módulo de lectura de sensores híbridos y digitales bajo arquitectura `asyncio` (intervalo de muestreo: 15 s).
- Sensores analógicos (I2C / ADC Mux):
    - pH: cálculo basado en voltaje (3.3 V ref) con pendiente y offset.
    - Oxígeno disuelto (DO): mapeo de valores ADC a mg/L.
    - Gases: lectura multiplexada para Amoniaco (NH3) y Sulfuro de Hidrógeno (H2S/S2H) en ppm.
- Sensores RS485 (UART):
    - Implementación de protocolo tipo Modbus sobre UART2.
    - Lectura de nivel de líquido (convertido de mm a cm).
    - Lectura de temperatura del sensor.
- Lógica de validación de rangos y reintentos de lectura (hasta 3 intentos).

### Changed (Interfaz)
- Web App: rediseño del frontend para visualizar la telemetría de los nuevos sensores (pH, DO, Nivel, Temp, Gases).
- LCD: actualización de la interfaz física para rotar/mostrar los nuevos valores capturados.

### Fixed
- Actuadores: corrección en la lógica de temporización para el control de encendido/apagado.

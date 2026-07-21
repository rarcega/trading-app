# Trading App - Análisis Técnico

Aplicación de trading en Python con análisis técnico automático y modo simulación.

## Características

- **Modo Simulación**: Opera con datos reales de yfinance sin arriesgar dinero
- **Análisis Técnico**: RSI, MACD, Bollinger Bands, SMA/EMA
- **Estrategia de Rotación**: Compra/vende según señales técnicas (máx 5 posiciones)
- **GUI PyQt6**: Interfaz gráfica profesional con gráficos en tiempo real
- **Base de Datos**: Historial completo de trades y señales en SQLite

## Requisitos

- Python 3.10 o superior
- Interactive Brokers account (para modo real)

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/rarcega/trading-app.git
cd trading_app

# Crear entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py
```

## Uso

1. **Conectar**: Haz clic en "Conectar" en la barra de herramientas
2. **Configurar**: Ajusta el monto de inversión y número de posiciones
3. **Iniciar**: Haz clic en "Iniciar Estrategia" para comenzar el trading automático
4. **Monitorea**: Observa las posiciones, trades y señales en las pestañas

## Modos de Operación

### Simulación (Default)
- Usa datos de mercado reales vía yfinance
- Ejecuta órdenes simuladas sin dinero real
- Ideal para probar la estrategia antes de invertir

### Real (IBKR)
- Requiere Interactive Brokers Gateway o TWS ejecutándose
- Configura `use_simulation = False` en `config.py`
- Conéctate a IBKR en el puerto 7497 (TWS) o 4001 (Gateway)

## Estrategia

### Señales de COMPRA (mínimo 2.5 puntos):
- RSI < 30 (sobreventa): +1 punto
- MACD cruce alcista: +1 punto
- Precio en banda inferior de Bollinger (<20%): +1 punto
- SMA alcista (corto > largo): +0.5 punto

### Señales de VENTA (mínimo 2.5 puntos):
- RSI > 70 (sobrecompra): +1 punto
- MACD cruce bajista: +1 punto
- Precio en banda superior de Bollinger (>80%): +1 punto
- SMA bajista (corto < largo): +0.5 punto

## Configuración

Edita `config.py` para personalizar:

```python
# Inversión total
trading.investment_amount = 10000.0

# Máximo de posiciones simultáneas
trading.max_positions = 5

# Intervalo de revisión (segundos)
trading.check_interval_seconds = 60

# Watchlist de acciones
trading.watchlist = ["AAPL", "MSFT", "GOOGL", ...]
```

## Estructura

```
trading_app/
├── main.py                 # Punto de entrada
├── config.py              # Configuración
├── requirements.txt       # Dependencias
├── database/              # Modelos SQLite
├── broker/                # IBKR + Simulación
├── analysis/              # Indicadores técnicos
├── strategy/              # Estrategia de rotación
├── gui/                   # PyQt6 con gráficos
└── utils/                 # Helpers
```

## Licencia

MIT

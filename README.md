# Trading App - Análisis Técnico

Aplicación de trading en Python con análisis técnico automático y modo simulación.

## Características

- **Modo Simulación**: Opera con datos reales de yfinance sin arriesgar dinero
- **Análisis Técnico**: RSI, MACD, Bollinger Bands, SMA/EMA
- **Estrategia de Rotación**: Compra/vende según señales técnicas (máx 5 posiciones)
- **GUI PyQt6**: Interfaz gráfica de escritorio con gráficos
- **Web App**: Interfaz web accesible desde móvil o navegador
- **Base de Datos**: Historial completo de trades y señales en SQLite

## Requisitos

- Python 3.10 o superior

## Instalación

```bash
git clone https://github.com/rarcega/trading-app.git
cd trading_app
pip install -r requirements.txt
```

## Ejecución

### App de escritorio
```bash
python main.py
```

### Web App (accesible desde móvil)
```bash
python run_web.py
```
Accede en: http://localhost:8000

## Uso

1. **Conectar**: Haz clic en "Conectar"
2. **Configurar**: Ajusta el monto, posiciones y parámetros de la estrategia
3. **Iniciar**: Haz clic en "Iniciar Estrategia"
4. **Monitorea**: Posiciones, señales, historial y logs en tiempo real

## Web App - Acceso desde móvil

1. Ejecuta `python run_web.py`
2. Desde el móvil, accede a `http://IP-DEL-PC:8000`
3. Para acceso externo, usa un VPS o configura port forwarding

## Despliegue 24/7 en la nube

### DigitalOcean ($5/mes)
```bash
# Crear VPS Ubuntu
# Instalar Python
sudo apt update && sudo apt install python3-pip
git clone https://github.com/rarcega/trading-app.git
cd trading_app
pip install -r requirements.txt
nohup python run_web.py &
```

### Render (free tier)
- Conecta tu repositorio GitHub
- Build: `pip install -r requirements.txt`
- Start: `python run_web.py`

## Configuración

Todos los parámetros se guardan en `data/config.json` y se persisten entre sesiones.

## Estrategia

### Señales de COMPRA (umbral configurable, default 2.0):
- RSI < 35 (sobreventa): +1 punto
- MACD cruce alcista: +1 punto
- Precio en banda inferior de Bollinger (<20%): +1 punto
- SMA alcista (corto > largo): +0.5 punto

### Señales de VENTA (umbral configurable, default 2.0):
- RSI > 65 (sobrecompra): +1 punto
- MACD cruce bajista: +1 punto
- Precio en banda superior de Bollinger (>80%): +1 punto
- SMA bajista (corto < largo): +0.5 punto

## Estructura

```
trading_app/
├── main.py                 # App de escritorio
├── run_web.py              # Web app
├── config.py               # Configuración con persistencia JSON
├── requirements.txt        # Dependencias
├── database/               # Modelos SQLite
├── broker/                 # IBKR + Simulación
├── analysis/               # Indicadores técnicos
├── strategy/               # Estrategia de rotación
├── gui/                    # PyQt6 de escritorio
├── web/                    # Web app (FastAPI + HTML)
│   ├── app.py              # API endpoints
│   └── templates/          # Frontend HTML
└── data/                   # BD y config (gitignored)
```

## Licencia

MIT

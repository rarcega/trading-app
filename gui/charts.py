import pandas as pd
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
from PyQt6.QtCore import Qt
from ..config import config
from ..analysis.indicators import TechnicalIndicators


class ChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.indicators = TechnicalIndicators()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        self.symbol_label = QLabel("Selecciona una posición para ver el gráfico")
        self.symbol_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header.addWidget(self.symbol_label)

        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["1 día", "1 hora", "5 minutos"])
        self.timeframe_combo.currentIndexChanged.connect(self.on_timeframe_changed)
        header.addWidget(self.timeframe_combo)
        layout.addLayout(header)

        self.chart_widget = pg.PlotWidget()
        self.chart_widget.setBackground("#1e1e1e")
        self.chart_widget.showGrid(x=True, y=True, alpha=0.3)
        self.chart_widget.addLegend()
        layout.addWidget(self.chart_widget)

        self.rsi_widget = pg.PlotWidget()
        self.rsi_widget.setBackground("#1e1e1e")
        self.rsi_widget.setMaximumHeight(150)
        layout.addWidget(self.rsi_widget)

        self.current_symbol = None
        self.current_df = None

    def update_chart(self, symbol: str, df: pd.DataFrame):
        self.current_symbol = symbol
        self.current_df = df.copy()
        self.symbol_label.setText(f"Gráfico: {symbol}")
        self.render_chart()

    def render_chart(self):
        if self.current_df is None or self.current_df.empty:
            return

        df = self.current_df.copy()
        df = self.indicators.calculate_all(df)
        df = df.dropna()

        if df.empty:
            return

        self.chart_widget.clear()
        self.rsi_widget.clear()

        x = list(range(len(df)))

        close = df["close"].values
        self.chart_widget.plot(x, close, pen=pg.mkPen("white", width=2), name="Precio")

        if "SMA_SHORT" in df.columns:
            sma_short = df["SMA_SHORT"].values
            self.chart_widget.plot(x, sma_short, pen=pg.mkPen("yellow", width=1, style=Qt.PenStyle.DashLine), name=f"SMA {config.strategy.sma_short}")

        if "SMA_LONG" in df.columns:
            sma_long = df["SMA_LONG"].values
            self.chart_widget.plot(x, sma_long, pen=pg.mkPen("orange", width=1, style=Qt.PenStyle.DashLine), name=f"SMA {config.strategy.sma_long}")

        if "BB_UPPER" in df.columns:
            bb_upper = df["BB_UPPER"].values
            bb_lower = df["BB_LOWER"].values
            bb_mid = df["BB_MID"].values
            self.chart_widget.plot(x, bb_upper, pen=pg.mkPen("cyan", width=1, style=Qt.PenStyle.DotLine), name="BB Superior")
            self.chart_widget.plot(x, bb_lower, pen=pg.mkPen("cyan", width=1, style=Qt.PenStyle.DotLine), name="BB Inferior")
            self.chart_widget.plot(x, bb_mid, pen=pg.mkPen("cyan", width=1, style=Qt.PenStyle.DashDotLine), name="BB Media")

        if "RSI" in df.columns:
            rsi = df["RSI"].values
            rsi_item = self.rsi_widget.plot(x, rsi, pen=pg.mkPen("purple", width=2), name="RSI")

            overbought = [config.strategy.rsi_overbought] * len(x)
            oversold = [config.strategy.rsi_oversold] * len(x)
            self.rsi_widget.plot(x, overbought, pen=pg.mkPen("red", width=1, style=Qt.PenStyle.DashLine))
            self.rsi_widget.plot(x, oversold, pen=pg.mkPen("green", width=1, style=Qt.PenStyle.DashLine))

        buys = df[df.get("MACD_HIST", pd.Series()) > 0].index
        sells = df[df.get("MACD_HIST", pd.Series()) < 0].index

    def on_timeframe_changed(self, index):
        pass

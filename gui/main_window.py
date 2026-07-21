from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTabWidget, QGroupBox, QLabel, QPushButton, QComboBox,
    QDoubleSpinBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QStatusBar, QToolBar, QTextEdit,
    QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QAction, QColor, QFont
from config import config
from database.db_manager import DatabaseManager
from broker.simulation_connector import SimulationConnector
from broker.order_manager import OrderManager
from analysis.signals import SignalGenerator
from strategy.rotation_strategy import RotationStrategy
from gui.charts import ChartWidget


class StrategyThread(QThread):
    action_signal = pyqtSignal(dict)
    log_signal = pyqtSignal(str)

    def __init__(self, strategy: RotationStrategy):
        super().__init__()
        self.strategy = strategy

    def run(self):
        while self.strategy.is_running():
            try:
                actions = self.strategy.execute()
                for action in actions:
                    self.action_signal.emit(action)
                    self.log_signal.emit(
                        f"[{action['action']}] {action['symbol']} "
                        f"x{action['quantity']} @ ${action['price']:.2f} "
                        f"- {', '.join(action['reasons'])}"
                    )
            except Exception as e:
                self.log_signal.emit(f"Error: {e}")
            self.strategy.broker.update_positions_prices() if hasattr(self.strategy.broker, 'update_positions_prices') else None
            self.msleep(config.trading.check_interval_seconds * 1000)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trading App - Análisis Técnico")
        self.setMinimumSize(1200, 800)

        self.db = DatabaseManager(config.db_path)
        self.broker = SimulationConnector() if config.trading.use_simulation else None
        self.order_manager = OrderManager(self.broker, self.db)
        self.signal_generator = SignalGenerator(self.db)
        self.strategy = RotationStrategy(
            self.broker, self.order_manager, self.signal_generator, self.db
        )
        self.strategy_thread = None

        self.setup_ui()
        self.setup_connections()
        self.update_watchlist_table()
        self.update_portfolio_table()
        self.update_trades_table()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)

        self.connect_action = QAction("Conectar", self)
        self.toolbar.addAction(self.connect_action)

        self.disconnect_action = QAction("Desconectar", self)
        self.disconnect_action.setEnabled(False)
        self.toolbar.addAction(self.disconnect_action)

        self.toolbar.addSeparator()

        self.start_action = QAction("Iniciar Estrategia", self)
        self.start_action.setEnabled(False)
        self.toolbar.addAction(self.start_action)

        self.stop_action = QAction("Detener Estrategia", self)
        self.stop_action.setEnabled(False)
        self.toolbar.addAction(self.stop_action)

        self.toolbar.addSeparator()

        self.mode_label = QLabel(" MODO: SIMULACIÓN ")
        self.mode_label.setStyleSheet(
            "background-color: #ff9800; color: white; padding: 4px 8px; "
            "font-weight: bold; border-radius: 3px;"
        )
        self.toolbar.addWidget(self.mode_label)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        config_group = QGroupBox("Configuración")
        config_layout = QVBoxLayout()

        amount_layout = QHBoxLayout()
        amount_layout.addWidget(QLabel("Inversión total ($):"))
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(1000, 1000000)
        self.amount_spin.setValue(config.trading.investment_amount)
        self.amount_spin.setSingleStep(1000)
        amount_layout.addWidget(self.amount_spin)
        config_layout.addLayout(amount_layout)

        max_pos_layout = QHBoxLayout()
        max_pos_layout.addWidget(QLabel("Máx. posiciones:"))
        self.max_pos_spin = QSpinBox()
        self.max_pos_spin.setRange(1, 20)
        self.max_pos_spin.setValue(config.trading.max_positions)
        max_pos_layout.addWidget(self.max_pos_spin)
        config_layout.addLayout(max_pos_layout)

        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Intervalo (seg):"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(10, 3600)
        self.interval_spin.setValue(config.trading.check_interval_seconds)
        interval_layout.addWidget(self.interval_spin)
        config_layout.addLayout(interval_layout)

        config_group.setLayout(config_layout)
        left_layout.addWidget(config_group)

        watchlist_group = QGroupBox("Watchlist")
        watchlist_layout = QVBoxLayout()

        self.watchlist_table = QTableWidget()
        self.watchlist_table.setColumnCount(1)
        self.watchlist_table.setHorizontalHeaderLabels(["Símbolo"])
        self.watchlist_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.watchlist_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.watchlist_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.watchlist_table.setMaximumHeight(200)
        watchlist_layout.addWidget(self.watchlist_table)

        add_layout = QHBoxLayout()
        self.watchlist_input = QLineEdit()
        self.watchlist_input.setPlaceholderText("Ej: AAPL, SAN.MC, SAP.DE")
        add_layout.addWidget(self.watchlist_input)
        self.add_watchlist_btn = QPushButton("+")
        self.add_watchlist_btn.setFixedWidth(40)
        self.add_watchlist_btn.setStyleSheet("font-weight: bold; font-size: 16px;")
        add_layout.addWidget(self.add_watchlist_btn)
        watchlist_layout.addLayout(add_layout)

        self.remove_watchlist_btn = QPushButton("Quitar seleccionada")
        watchlist_layout.addWidget(self.remove_watchlist_btn)

        watchlist_group.setLayout(watchlist_layout)
        left_layout.addWidget(watchlist_group)

        portfolio_group = QGroupBox("Posiciones")
        portfolio_layout = QVBoxLayout()
        self.portfolio_table = QTableWidget()
        self.portfolio_table.setColumnCount(6)
        self.portfolio_table.setHorizontalHeaderLabels(
            ["Símbolo", "Cantidad", "Precio Entrada", "Precio Actual", "P&L", "P&L %"]
        )
        self.portfolio_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.portfolio_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        portfolio_layout.addWidget(self.portfolio_table)
        portfolio_group.setLayout(portfolio_layout)
        left_layout.addWidget(portfolio_group)

        summary_group = QGroupBox("Resumen Cuenta")
        summary_layout = QVBoxLayout()
        self.summary_label = QLabel("Efectivo: $0.00 | Posiciones: $0.00 | Total: $0.00")
        self.summary_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        summary_layout.addWidget(self.summary_label)
        summary_group.setLayout(summary_layout)
        left_layout.addWidget(summary_group)

        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.tabs = QTabWidget()

        self.chart_widget = ChartWidget()
        self.tabs.addTab(self.chart_widget, "Gráfico")

        trades_tab = QWidget()
        trades_layout = QVBoxLayout(trades_tab)
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(7)
        self.trades_table.setHorizontalHeaderLabels(
            ["Fecha", "Símbolo", "Tipo", "Cantidad", "Precio", "Total", "Notas"]
        )
        self.trades_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.trades_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        trades_layout.addWidget(self.trades_table)
        self.tabs.addTab(trades_tab, "Historial")

        signals_tab = QWidget()
        signals_layout = QVBoxLayout(signals_tab)
        self.signals_table = QTableWidget()
        self.signals_table.setColumnCount(6)
        self.signals_table.setHorizontalHeaderLabels(
            ["Fecha", "Símbolo", "Señal", "RSI", "MACD", "Precio"]
        )
        self.signals_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.signals_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        signals_layout.addWidget(self.signals_table)
        self.tabs.addTab(signals_tab, "Señales")

        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: Consolas;")
        log_layout.addWidget(self.log_text)
        self.tabs.addTab(log_tab, "Log")

        right_layout.addWidget(self.tabs)
        splitter.addWidget(right_panel)

        splitter.setSizes([400, 800])

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Desconectado")

    def setup_connections(self):
        self.connect_action.triggered.connect(self.connect_broker)
        self.disconnect_action.triggered.connect(self.disconnect_broker)
        self.start_action.triggered.connect(self.start_strategy)
        self.stop_action.triggered.connect(self.stop_strategy)
        self.portfolio_table.cellClicked.connect(self.on_position_clicked)
        self.add_watchlist_btn.clicked.connect(self.add_to_watchlist)
        self.remove_watchlist_btn.clicked.connect(self.remove_from_watchlist)
        self.watchlist_input.returnPressed.connect(self.add_to_watchlist)

    def add_to_watchlist(self):
        symbol = self.watchlist_input.text().strip().upper()
        if not symbol:
            return
        if "," in symbol:
            symbols = [s.strip() for s in symbol.split(",") if s.strip()]
            for s in symbols:
                if s not in config.trading.watchlist:
                    config.trading.watchlist.append(s)
                    self.log(f"Añadido a watchlist: {s}")
        else:
            if symbol not in config.trading.watchlist:
                config.trading.watchlist.append(symbol)
                self.log(f"Añadido a watchlist: {symbol}")
            else:
                QMessageBox.information(self, "Info", f"{symbol} ya está en la watchlist")
        self.watchlist_input.clear()
        self.update_watchlist_table()

    def remove_from_watchlist(self):
        row = self.watchlist_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Selecciona una acción para quitar")
            return
        symbol = self.watchlist_table.item(row, 0).text()
        if symbol in config.trading.watchlist:
            config.trading.watchlist.remove(symbol)
            self.log(f"Eliminado de watchlist: {symbol}")
            self.update_watchlist_table()

    def update_watchlist_table(self):
        self.watchlist_table.setRowCount(len(config.trading.watchlist))
        for i, symbol in enumerate(config.trading.watchlist):
            self.watchlist_table.setItem(i, 0, QTableWidgetItem(symbol))

    def connect_broker(self):
        if self.broker.connect():
            self.connect_action.setEnabled(False)
            self.disconnect_action.setEnabled(True)
            self.start_action.setEnabled(True)
            self.statusBar.showMessage("Conectado - Modo Simulación" if config.trading.use_simulation else "Conectado - IBKR")
            self.update_account_summary()
            self.log("Conexión establecida correctamente")
        else:
            QMessageBox.critical(self, "Error", "No se pudo conectar al broker")

    def disconnect_broker(self):
        self.stop_strategy()
        self.broker.disconnect()
        self.connect_action.setEnabled(True)
        self.disconnect_action.setEnabled(False)
        self.start_action.setEnabled(False)
        self.statusBar.showMessage("Desconectado")
        self.log("Desconectado del broker")

    def start_strategy(self):
        self.strategy.start()
        self.strategy_thread = StrategyThread(self.strategy)
        self.strategy_thread.action_signal.connect(self.on_action)
        self.strategy_thread.log_signal.connect(self.log)
        self.strategy_thread.start()
        self.start_action.setEnabled(False)
        self.stop_action.setEnabled(True)
        self.log("Estrategia iniciada")

    def stop_strategy(self):
        if self.strategy_thread and self.strategy_thread.isRunning():
            self.strategy.stop()
            self.strategy_thread.wait(3000)
            self.start_action.setEnabled(True)
            self.stop_action.setEnabled(False)
            self.log("Estrategia detenida")

    def on_action(self, action: dict):
        self.update_portfolio_table()
        self.update_trades_table()
        self.update_account_summary()
        self.log(f"Operación: {action['action']} {action['symbol']} x{action['quantity']}")

    def on_position_clicked(self, row, col):
        symbol = self.portfolio_table.item(row, 0)
        if symbol:
            symbol_text = symbol.text()
            df = self.broker.get_historical_data(symbol_text)
            if df is not None:
                self.chart_widget.update_chart(symbol_text, df)

    def update_portfolio_table(self):
        positions = self.db.get_positions()
        self.portfolio_table.setRowCount(len(positions))
        for i, pos in enumerate(positions):
            self.portfolio_table.setItem(i, 0, QTableWidgetItem(pos.symbol))
            self.portfolio_table.setItem(i, 1, QTableWidgetItem(f"{pos.quantity:.0f}"))
            self.portfolio_table.setItem(i, 2, QTableWidgetItem(f"${pos.avg_price:.2f}"))
            self.portfolio_table.setItem(i, 3, QTableWidgetItem(f"${pos.current_price:.2f}"))

            pnl_item = QTableWidgetItem(f"${pos.unrealized_pnl:.2f}")
            if pos.unrealized_pnl >= 0:
                pnl_item.setForeground(QColor("green"))
            else:
                pnl_item.setForeground(QColor("red"))
            self.portfolio_table.setItem(i, 4, pnl_item)

            pnl_pct_item = QTableWidgetItem(f"{pos.unrealized_pnl_pct:.2f}%")
            if pos.unrealized_pnl_pct >= 0:
                pnl_pct_item.setForeground(QColor("green"))
            else:
                pnl_pct_item.setForeground(QColor("red"))
            self.portfolio_table.setItem(i, 5, pnl_pct_item)

    def update_trades_table(self):
        trades = self.db.get_trades(limit=50)
        self.trades_table.setRowCount(len(trades))
        for i, trade in enumerate(trades):
            self.trades_table.setItem(i, 0, QTableWidgetItem(str(trade.created_at)[:19]))
            self.trades_table.setItem(i, 1, QTableWidgetItem(trade.symbol))
            self.trades_table.setItem(i, 2, QTableWidgetItem(trade.trade_type))
            self.trades_table.setItem(i, 3, QTableWidgetItem(f"{trade.quantity:.0f}"))
            self.trades_table.setItem(i, 4, QTableWidgetItem(f"${trade.price:.2f}"))
            self.trades_table.setItem(i, 5, QTableWidgetItem(f"${trade.total_amount:.2f}"))
            self.trades_table.setItem(i, 6, QTableWidgetItem(trade.notes or ""))

    def update_account_summary(self):
        summary = self.broker.get_account_summary()
        self.summary_label.setText(
            f"Efectivo: ${summary.get('total_cash', 0):.2f} | "
            f"Posiciones: ${summary.get('positions_value', 0):.2f} | "
            f"Total: ${summary.get('account_value', 0):.2f}"
        )

    def log(self, message: str):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.statusBar.showMessage(message)

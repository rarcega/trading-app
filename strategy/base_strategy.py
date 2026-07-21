from abc import ABC, abstractmethod
from typing import Optional
from ..broker.order_manager import OrderManager
from ..analysis.signals import SignalGenerator
from ..database.db_manager import DatabaseManager


class BaseStrategy(ABC):
    def __init__(self, broker, order_manager: OrderManager,
                 signal_generator: SignalGenerator, db_manager: DatabaseManager):
        self.broker = broker
        self.order_manager = order_manager
        self.signal_generator = signal_generator
        self.db = db_manager
        self.running = False

    @abstractmethod
    def execute(self):
        pass

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def is_running(self) -> bool:
        return self.running

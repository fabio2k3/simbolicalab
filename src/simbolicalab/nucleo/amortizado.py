from __future__ import annotations

class LibroAmortizado:
    def __init__(self, potencial_inicial: float = 0.0) -> None:
        self.potencial_inicial = potencial_inicial
        self.potencial = potencial_inicial
        self.costos_reales: list[float] = []
        self.costos_amortizados: list[float] = []

    def registrar(self, costo_real: float, potencial_nuevo: float ) -> float:
        amortizado = costo_real + potencial_nuevo - self.potencial
        self.costos_reales.append(costo_real)
        self.costos_amortizados.append(amortizado)
        self.potencial = potencial_nuevo
        return amortizado

    @property
    def operaciones(self) -> int:
        return len(self.costos_reales)

    @property
    def total_real(self) -> float:
        return sum(self.costos_reales)

    @property
    def total_amortizado(self) -> float:
        return sum(self.costos_amortizados)

    @property
    def max_real(self) -> float:
        return max(self.costos_reales, default=0.0)

    @property
    def max_amortizado(self) -> float:
        return max(self.costos_amortizados,default=0.0)

    def suma_valida(self, tolerancia:float = 1e-9) -> bool:
        return self.potencial >= self.potencial_inicial - tolerancia

    def residuo_del_telescopio(self) -> float:
        return self.total_amortizado - self.total_real - (self.potencial - self.potencial_inicial)
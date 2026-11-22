"""Steady process-stream pinch targeting by shifted-temperature heat cascade.

Implements *energy targets*, not heat-exchanger network synthesis or design
of individual matches. Process hot streams cannot be counted again as an
independent evaporator heat source. Constant sensible heat-capacity rates,
fully simultaneous availability and freely matched process streams are assumed.

Reference: Linnhoff and Hindmarsh (1983), doi:10.1016/0009-2509(83)80185-7.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from math import isclose, isfinite


@dataclass(frozen=True)
class ProcessStream:
    name: str
    kind: str
    supply_C: float
    target_C: float
    heat_capacity_rate_kW_K: float

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("process stream must have an identity")
        if self.kind not in ("hot", "cold"):
            raise ValueError("stream kind must be 'hot' or 'cold'")
        for v in (self.supply_C, self.target_C, self.heat_capacity_rate_kW_K):
            if isinstance(v, bool) or not isfinite(v):
                raise ValueError("nonfinite stream")
        if min(self.supply_C, self.target_C) <= -273.15:
            raise ValueError("below absolute zero")
        if self.heat_capacity_rate_kW_K <= 0:
            raise ValueError("heat capacity rate must be positive")
        if (self.kind == "hot" and self.supply_C <= self.target_C) or (
            self.kind == "cold" and self.supply_C >= self.target_C
        ):
            raise ValueError("hot must cool; cold must heat")


def _shifted(s: ProcessStream, dtmin_K: float) -> tuple[float, float, float]:
    delta = -dtmin_K / 2 if s.kind == "hot" else dtmin_K / 2
    return s.supply_C + delta, s.target_C + delta, s.heat_capacity_rate_kW_K


def heat_cascade(streams: list[ProcessStream] | tuple[ProcessStream, ...],
                 delta_t_min_K: float) -> dict:
    if not isinstance(delta_t_min_K, (float, int)) or isinstance(delta_t_min_K, bool) or (
        not isfinite(delta_t_min_K) or delta_t_min_K <= 0
    ):
        raise ValueError("delta T minimum must be finite and positive")
    if not streams or not all(isinstance(s, ProcessStream) for s in streams):
        raise ValueError("at least one valid stream needed")
    if len({s.name.casefold() for s in streams}) != len(streams):
        raise ValueError("duplicate process stream name")
    hot = [s for s in streams if s.kind == "hot"]
    cold = [s for s in streams if s.kind == "cold"]
    if not cold:
        raise ValueError("at least one cold-process stream is required")
    shifted = [_shifted(s, float(delta_t_min_K)) for s in streams]
    levels = sorted({v for a, b, _ in shifted for v in (a, b)}, reverse=True)
    intervals = []
    cascade = [0.0]
    for high, low in zip(levels, levels[1:]):
        if high <= low:
            raise ArithmeticError("unordered temperature intervals")
        hot_cp = sum(cp for s, (a, z, cp) in zip(streams, shifted)
                     if s.kind == "hot" and a >= high and z <= low)
        cold_cp = sum(cp for s, (a, z, cp) in zip(streams, shifted)
                      if s.kind == "cold" and z >= high and a <= low)
        dq = (hot_cp - cold_cp) * (high - low)
        cascade.append(cascade[-1] + dq)
        intervals.append(dict(upper_shifted_C=high, lower_shifted_C=low,
             hot_cp_rate_kW_K=hot_cp, cold_cp_rate_kW_K=cold_cp,
             net_heat_kW=dq, unadjusted_residual_kW=cascade[-1]))
    required_hot = max(0.0, -min(cascade))
    adjusted = [x + required_hot for x in cascade]
    required_cold = adjusted[-1]
    if required_cold < -1e-7:
        raise ArithmeticError("negative remaining cold utility")
    total_hot = sum((s.supply_C - s.target_C) * s.heat_capacity_rate_kW_K for s in hot)
    total_cold = sum((s.target_C - s.supply_C) * s.heat_capacity_rate_kW_K for s in cold)
    recovered_cold = total_cold - required_hot
    recovered_hot = total_hot - required_cold
    if not isclose(recovered_cold, recovered_hot, abs_tol=1e-7, rel_tol=1e-10):
        raise ArithmeticError("pinch cascade violates conserved process heat")
    if recovered_cold < -1e-7:
        raise ArithmeticError("negative heat recovery")
    pinches = [levels[i] for i, h in enumerate(adjusted)
               if 0 < i < len(adjusted)-1 and abs(h) <= 1e-7]
    return dict(delta_t_min_K=float(delta_t_min_K),
       total_process_hot_kW=total_hot,total_process_cold_kW=total_cold,
       maximum_internal_process_heat_recovery_kW=max(0.0, recovered_cold),
       minimum_external_heating_kW=required_hot,
       minimum_external_cooling_kW=max(0.0, required_cold),
       heat_balance_residual_kW=total_hot+required_hot-total_cold-required_cold,
       pinch_shifted_temperatures_C=pinches,temperature_intervals=intervals,
       process_streams=[asdict(s) for s in streams],
       heat_exchanger_network_designed=False,
       cross_pinch_transfer_prohibited_in_utility_target=True,
       independent_external_HP_source_required=True,
       finite_exchanger_UA_or_pressure_drop_calculated=False)

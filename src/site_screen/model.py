"""Conservative first-pass industrial high-temperature heat-pump screening.

The heat pump COP is an ASSUMED fraction of a Carnot COP, *not* the
R600/R600a/R718 EOS work from CarnotBatteryLab and not an experimentally
validated compressor curve. Heat-source supply/return temperatures are
available bulk-stream boundaries; no process pinch cascade is solved.

All calculations are deterministic and use SI-compatible kW/kWh units.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from math import isfinite


@dataclass(frozen=True)
class Site:
    site_id: str
    source_supply_C: float
    source_return_C: float
    source_flow_kg_s: float
    process_return_C: float
    process_supply_C: float
    process_demand_kW: float
    operating_hours_per_year: float
    electricity_eur_per_kWh: float
    boiler_fuel_eur_per_kWh: float
    boiler_efficiency: float
    assumed_carnot_fraction: float = 0.45
    source_cp_kJ_kgK: float = 4.18
    hot_approach_K: float = 5.0
    cold_approach_K: float = 5.0
    discount_rate: float = 0.08
    lifetime_years: int = 15
    incremental_opex_eur_per_year: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.site_id, str) or not self.site_id.strip():
            raise ValueError("site_id must be nonempty")
        for k, v in asdict(self).items():
            if k == "site_id":
                continue
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not isfinite(v):
                raise ValueError(f"{self.site_id}: {k} must be a finite number")
        if not (self.source_supply_C > self.source_return_C):
            raise ValueError(f"{self.site_id}: source supply must exceed return")
        if not (self.process_supply_C > self.process_return_C):
            raise ValueError(f"{self.site_id}: process supply must exceed return")
        if min(self.source_flow_kg_s, self.process_demand_kW) <= 0:
            raise ValueError(f"{self.site_id}: mass flow and demand must be positive")
        if not (0 < self.operating_hours_per_year <= 8760):
            raise ValueError(f"{self.site_id}: annual hours must lie in (0,8760]")
        if self.source_cp_kJ_kgK <= 0 or min(self.hot_approach_K, self.cold_approach_K) <= 0:
            raise ValueError(f"{self.site_id}: heat capacity and pinches must be positive")
        if not (0 < self.boiler_efficiency <= 1 and 0 < self.assumed_carnot_fraction <= 1):
            raise ValueError(f"{self.site_id}: efficiencies/fractions must lie in (0,1]")
        if self.boiler_fuel_eur_per_kWh < 0 or self.discount_rate < 0:
            raise ValueError(f"{self.site_id}: fuel price/discount rate must be nonnegative")
        if self.incremental_opex_eur_per_year < 0:
            raise ValueError(f"{self.site_id}: incremental fixed OPEX must be nonnegative")
        if not isinstance(self.lifetime_years, int) or not (1 <= self.lifetime_years <= 60):
            raise ValueError(f"{self.site_id}: lifetime_years must be integer 1..60")


def _pv_annuity_factor(n_years: int, discount: float) -> float:
    """Present value of one unit of annual end-of-year savings over n years."""
    if discount == 0:
        return float(n_years)
    return sum((1.0 + discount) ** (-year) for year in range(1, n_years + 1))


def screen_site(site: Site) -> dict:
    """Screen a site with bounded thermodynamic and annual-cashflow accounting.

    Status "full_heat_demand_proxy" means *only* that this steady surrogate
    meets the specified process duty. It never establishes a qualified
    refrigerant/compressor operating point, heat-exchanger design or cost.
    """
    base = dict(
        site_id=site.site_id,
        source_heat_available_kW=site.source_flow_kg_s * site.source_cp_kJ_kgK
        * (site.source_supply_C - site.source_return_C),
        process_demand_kW=site.process_demand_kW,
        assumptions=dict(assumed_carnot_fraction=site.assumed_carnot_fraction,
            condenser_approach_K=site.hot_approach_K,
            evaporator_approach_K=site.cold_approach_K,
            source_cp_kJ_kgK=site.source_cp_kJ_kgK,
            discount_rate=site.discount_rate, lifetime_years=site.lifetime_years),
        research_only=True, experimentally_validated=False,
        refrigerant_compressor_map_verified=False,
        industrial_pinches_resolved=False, auxiliaries_included=False,
        hourly_dispatch_optimized=False, manufacturer_capex_estimated=False,
    )
    cond_K = site.process_supply_C + site.hot_approach_K + 273.15
    evap_K = site.source_return_C - site.cold_approach_K + 273.15
    base["condenser_proxy_K"] = cond_K
    base["evaporator_proxy_K"] = evap_K
    if evap_K <= 0 or cond_K <= evap_K:
        return dict(base, status="rejected", reasons=["invalid_temperature_lift"],
                    COP_assumed=None, heat_pump_heat_kW=0.0)
    carnot_COP = cond_K / (cond_K - evap_K)
    assumed_COP = site.assumed_carnot_fraction * carnot_COP
    base["carnot_heating_COP_ideal"] = carnot_COP
    base["COP_assumed"] = assumed_COP
    if assumed_COP <= 1.0:
        return dict(base, status="rejected", reasons=["assumed_COP_at_or_below_one"],
                    heat_pump_heat_kW=0.0)

    # First law: Q_hot = Q_source + W, Q_source/Q_hot = 1 - 1/COP.
    source_fraction = 1.0 - 1.0 / assumed_COP
    maximum_heat_from_source_kW = base["source_heat_available_kW"] / source_fraction
    hot_kW = min(site.process_demand_kW, maximum_heat_from_source_kW)
    electric_kW = hot_kW / assumed_COP
    source_used_kW = hot_kW - electric_kW
    residual_boiler_kW = site.process_demand_kW - hot_kW
    if min(hot_kW, electric_kW, source_used_kW, residual_boiler_kW) < -1e-8:
        raise ArithmeticError("negative thermodynamic result")
    balance_kW = hot_kW - source_used_kW - electric_kW
    if abs(balance_kW) > 1e-8 * max(1, hot_kW):
        raise ArithmeticError("first-law closure failure")

    hours = site.operating_hours_per_year
    boiler_displaced_fuel_kWh_year = hot_kW / site.boiler_efficiency * hours
    hp_electricity_kWh_year = electric_kW * hours
    source_recovered_kWh_year = source_used_kW * hours
    baseline_fuel_kWh_year = site.process_demand_kW / site.boiler_efficiency * hours
    remaining_fuel_kWh_year = residual_boiler_kW / site.boiler_efficiency * hours
    annual_fuel_saving_eur = boiler_displaced_fuel_kWh_year * site.boiler_fuel_eur_per_kWh
    annual_HP_electricity_eur = hp_electricity_kWh_year * site.electricity_eur_per_kWh
    annual_net_saving_eur = (annual_fuel_saving_eur - annual_HP_electricity_eur
                            - site.incremental_opex_eur_per_year)
    pv_before_capex = annual_net_saving_eur * _pv_annuity_factor(
        site.lifetime_years, site.discount_rate)
    price_break_even = ((annual_fuel_saving_eur -
                         site.incremental_opex_eur_per_year) /
                        hp_electricity_kWh_year)

    return dict(base,
        status="full_heat_demand_proxy" if hot_kW >= site.process_demand_kW - 1e-8
               else "source_limited_proxy",
        reasons=[] if hot_kW >= site.process_demand_kW - 1e-8
                else ["source_heat_availability"],
        heat_pump_heat_kW=hot_kW, compressor_electric_kW=electric_kW,
        recovered_source_heat_kW=source_used_kW,
        residual_boiler_heat_kW=max(0.0, residual_boiler_kW),
        heat_pump_demand_fraction=hot_kW / site.process_demand_kW,
        first_law_residual_kW=balance_kW,
        boiler_fuel_displaced_kWh_per_year=boiler_displaced_fuel_kWh_year,
        hp_electricity_kWh_per_year=hp_electricity_kWh_year,
        recovered_source_kWh_per_year=source_recovered_kWh_year,
        baseline_boiler_fuel_kWh_per_year=baseline_fuel_kWh_year,
        hybrid_boiler_fuel_kWh_per_year=remaining_fuel_kWh_year,
        annual_fuel_cost_savings_eur=annual_fuel_saving_eur,
        annual_hp_electricity_cost_eur=annual_HP_electricity_eur,
        annual_incremental_fixed_opex_eur=site.incremental_opex_eur_per_year,
        annual_net_savings_before_capex_eur=annual_net_saving_eur,
        pv_net_savings_before_capex_eur=pv_before_capex,
        break_even_installed_capex_ceiling_eur=max(0.0, pv_before_capex),
        break_even_electricity_price_eur_per_kWh=price_break_even,
        positive_economic_break_even_ceiling=pv_before_capex > 0,
        complete_electricity_consumption_known=False,
        real_vendor_investment_cost_known=False,
    )

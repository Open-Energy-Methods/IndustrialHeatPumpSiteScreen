"""Industrial process integration + conditional tariff-block heat-pump dispatch.

"Optimized" here means a deterministic minimum-operating-cost ON/OFF
choice for each independent tariff block without thermal storage or
ramping constraints. It is NOT comprehensive industrial co-optimization.
All heat is supplied from either the heat pump or an existing boiler.
All process hot streams in the pinch cascade are excluded from the
independent heat-pump evaporator source.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, replace
from math import isfinite
from .pinch import ProcessStream, heat_cascade
from .model import _pv_annuity_factor


@dataclass(frozen=True)
class Source:
    """Independent residual waste-heat stream unavailable to process recovery."""
    supply_C: float
    return_C: float
    capacity_rate_kW_K: float

    def __post_init__(self):
        for x in (self.supply_C,self.return_C,self.capacity_rate_kW_K):
            if isinstance(x,bool) or not isfinite(x):
                raise ValueError("nonfinite independent heat source")
        if not (-273.15 < self.return_C < self.supply_C and self.capacity_rate_kW_K>0):
            raise ValueError("invalid independent source")
    @property
    def available_kW(self) -> float:
        return (self.supply_C-self.return_C)*self.capacity_rate_kW_K


@dataclass(frozen=True)
class TariffBlock:
    name: str
    hours: float
    electricity_eur_kWh: float
    load_fraction: float=1.0
    source_fraction: float=1.0

    def __post_init__(self):
        if not isinstance(self.name,str) or not self.name.strip():
            raise ValueError("tariff block needs name")
        for x in (self.hours,self.electricity_eur_kWh,
                  self.load_fraction,self.source_fraction):
            if isinstance(x,bool) or not isfinite(x):
                raise ValueError("nonfinite tariff block")
        if not 0<self.hours<=8760 or not 0<=self.load_fraction<=1 or not 0<=self.source_fraction<=1:
            raise ValueError("block hours/fractions out of bounds")


@dataclass(frozen=True)
class ProcessSite:
    site_id: str
    streams: tuple[ProcessStream,...]
    independent_source: Source
    tariff_blocks: tuple[TariffBlock,...]
    boiler_efficiency: float
    fuel_eur_kWh: float
    incremental_fixed_opex_eur_year: float=0.
    discount_rate: float=.08
    lifetime_years: int=15
    heat_pump_carnot_fraction: float=.45
    pinch_dt_min_K: float=10.
    condenser_approach_K: float=5.
    evaporator_approach_K: float=5.
    hp_nameplate_kW: float=1000.
    auxiliary_electric_fraction_of_compressor: float=.05
    hp_fixed_auxiliary_kW_when_on: float=0.

    def __post_init__(self):
        if not isinstance(self.site_id,str) or not self.site_id.strip():
            raise ValueError("process site needs site_id")
        if not self.streams or not self.tariff_blocks or not isinstance(self.independent_source,Source):
            raise ValueError("process streams, source and tariff blocks required")
        if not all(isinstance(x,ProcessStream) for x in self.streams) or not any(x.kind=="cold" for x in self.streams):
            raise ValueError("at least one cold-process stream required")
        if not all(isinstance(x,TariffBlock) for x in self.tariff_blocks):
            raise ValueError("invalid tariff block")
        if len({x.name.casefold() for x in self.tariff_blocks})!=len(self.tariff_blocks):
            raise ValueError("duplicate tariff name")
        x=(self.boiler_efficiency,self.fuel_eur_kWh,
           self.incremental_fixed_opex_eur_year,self.discount_rate,
           self.heat_pump_carnot_fraction,self.pinch_dt_min_K,
           self.condenser_approach_K,self.evaporator_approach_K,
           self.hp_nameplate_kW,self.auxiliary_electric_fraction_of_compressor,
           self.hp_fixed_auxiliary_kW_when_on)
        if any(isinstance(v,bool) or not isfinite(v) for v in x):
            raise ValueError("nonfinite site parameter")
        if not 0<self.boiler_efficiency<=1 or not 0<self.heat_pump_carnot_fraction<=1:
            raise ValueError("efficiency outside (0,1]")
        if min(self.fuel_eur_kWh,self.incremental_fixed_opex_eur_year,
               self.discount_rate,self.auxiliary_electric_fraction_of_compressor,
               self.hp_fixed_auxiliary_kW_when_on)<0:
            raise ValueError("costs, discount, auxiliary electrical terms nonnegative")
        if min(self.pinch_dt_min_K,self.condenser_approach_K,
               self.evaporator_approach_K,self.hp_nameplate_kW)<=0:
            raise ValueError("pinch, approaches and HP nameplate positive")
        if type(self.lifetime_years) is not int or not 1<=self.lifetime_years<=60:
            raise ValueError("lifetime 1..60 years")
        if sum(b.hours for b in self.tariff_blocks)>8760.000001:
            raise ValueError("total annual represented hours above 8760")


def _design_cop(site:ProcessSite)->tuple[float|None,dict]:
    # The maximum cold target provides a deliberately conservative
    # water-supply temperature envelope for *all* residual utility demand.
    process_max=max(x.target_C for x in site.streams if x.kind=="cold")
    tcond=process_max+site.condenser_approach_K+273.15
    tevap=site.independent_source.return_C-site.evaporator_approach_K+273.15
    meta=dict(hot_process_envelope_C=process_max,
              condensing_proxy_K=tcond,evaporating_proxy_K=tevap,
              COP_proxy_is_assumed_not_measured=True)
    if tevap<=0 or tcond<=tevap:
        return None,dict(meta,reason="invalid_temperature_lift")
    cop=site.heat_pump_carnot_fraction*tcond/(tcond-tevap)
    if cop<=1:
        return None,dict(meta,reason="COP_proxy_at_or_below_one",
                         computed_COP_proxy=cop)
    return cop,dict(meta,computed_COP_proxy=cop)


def evaluate_site(site:ProcessSite)->dict:
    """Thermal process pinch and conditional operational/economic threshold.

    Assumes a pre-existing *ideal* pinch heat-recovery network in BOTH
    baseline and HP scenarios. No charge to construct that network and
    no manufacturer price is inferred. This is a carefully restricted
    incremental HP assessment.
    """
    streams=list(site.streams)
    pinch=heat_cascade(streams,site.pinch_dt_min_K)
    cop,design=_design_cop(site)
    base_heat=pinch["minimum_external_heating_kW"]
    installed_capacity=site.hp_nameplate_kW
    annual=dict(baseline_boiler_fuel_kWh=0.,hybrid_boiler_fuel_kWh=0.,
        heat_pump_compressor_kWh=0.,heat_pump_auxiliary_kWh=0.,
        heat_pump_delivered_kWh=0.,external_source_heat_kWh=0.,
        cooling_utility_kWh=0.,baseline_heating_utility_kWh=0.,
        residual_heating_utility_kWh=0.,operating_savings_before_fixed_opex_eur=0.)
    rows=[]
    for block in site.tariff_blocks:
        # Uniform scale of all process Cp rates, NOT a resolved production plan.
        demand=base_heat*block.load_fraction
        process_cooling=pinch["minimum_external_cooling_kW"]*block.load_fraction
        source_available=site.independent_source.available_kW*block.source_fraction
        maximum_hp=0.
        if cop is not None and demand>0 and source_available>0:
            maximum_hp=min(demand,installed_capacity,
                           source_available/(1.-1./cop))
        compressor=maximum_hp/cop if cop is not None else 0.
        aux_variable=compressor*site.auxiliary_electric_fraction_of_compressor
        aux_fixed=(site.hp_fixed_auxiliary_kW_when_on if maximum_hp>0 else 0.)
        hypothetical_displacement=maximum_hp/site.boiler_efficiency*site.fuel_eur_kWh
        hypothetical_hp_cost=(compressor+aux_variable+aux_fixed)*block.electricity_eur_kWh
        # Dispatch by complete marginal/switching cost, no fractional load optimum
        # needed under affine demand and fixed marginal COP. When the fixed
        # overhead makes running at maximum uneconomic, stay OFF.
        on=bool(maximum_hp>0 and hypothetical_displacement>hypothetical_hp_cost+1e-12)
        heat=maximum_hp if on else 0.
        electric=compressor if on else 0.
        aux=aux_variable+aux_fixed if on else 0.
        source=heat-electric
        boiler=demand-heat
        if abs(heat-electric-source)>1e-8*max(1.,heat) or boiler < -1e-8:
            raise ArithmeticError("dispatch first-law or unmet-demand failure")
        fuel_saved=heat/site.boiler_efficiency*site.fuel_eur_kWh
        net_hour=fuel_saved-(electric+aux)*block.electricity_eur_kWh
        row=dict(name=block.name,hours=block.hours,
             demand_fraction=block.load_fraction,source_fraction=block.source_fraction,
             electricity_price_eur_kWh=block.electricity_eur_kWh,
             recovered_process_heat_kW=pinch["maximum_internal_process_heat_recovery_kW"]*block.load_fraction,
             baseline_external_heating_kW=demand,required_process_cooling_kW=process_cooling,
             independent_source_available_kW=source_available,
             hp_max_thermal_kW=maximum_hp,HP_dispatched_on=on,
             hp_delivered_kW=heat,hp_compressor_electric_kW=electric,
             hp_aux_electric_kW=aux,hp_external_source_heat_kW=source,
             boiler_remaining_kW=boiler,unserved_heat_kW=0.,
             heat_pump_energy_residual_kW=heat-electric-source,
             heat_supply_balance_residual_kW=demand-heat-boiler,
             net_hourly_cost_saving_eur=net_hour)
        rows.append(row)
        annual["baseline_boiler_fuel_kWh"]+=demand/site.boiler_efficiency*block.hours
        annual["hybrid_boiler_fuel_kWh"]+=boiler/site.boiler_efficiency*block.hours
        annual["heat_pump_compressor_kWh"]+=electric*block.hours
        annual["heat_pump_auxiliary_kWh"]+=aux*block.hours
        annual["heat_pump_delivered_kWh"]+=heat*block.hours
        annual["external_source_heat_kWh"]+=source*block.hours
        annual["cooling_utility_kWh"]+=process_cooling*block.hours
        annual["baseline_heating_utility_kWh"]+=demand*block.hours
        annual["residual_heating_utility_kWh"]+=boiler*block.hours
        annual["operating_savings_before_fixed_opex_eur"]+=net_hour*block.hours
    annual_saving=annual["operating_savings_before_fixed_opex_eur"]-site.incremental_fixed_opex_eur_year
    pv=annual_saving*_pv_annuity_factor(site.lifetime_years,site.discount_rate)
    baseline=annual["baseline_heating_utility_kWh"]
    electrification=(annual["heat_pump_delivered_kWh"]/baseline if baseline>0 else 0.)
    return dict(site_id=site.site_id,
        process_heat_cascade=pinch,independent_source=asdict(site.independent_source),
        assumed_COP=cop,design_envelope=design,
        hp_nameplate_kW=installed_capacity,annual=annual,dispatch_blocks=rows,
        annual_net_savings_eur=annual_saving,
        present_value_before_installed_capex_eur=pv,
        break_even_incremental_installed_capex_eur=max(0.,pv),
        positive_economic_screen=pv>0,
        fraction_external_heating_electrified=electrification,
        process_heat_balance_verified=all(abs(x["heat_supply_balance_residual_kW"])<1e-8 for x in rows),
        source_heat_balance_verified=all(abs(x["heat_pump_energy_residual_kW"])<1e-8 for x in rows),
        tariff_schedule_has_no_chronological_storage=False,
        chronological_thermal_storage_modeled=False,
        cost_optimisation_scope="independent-block HP on/off with unchanged boiler backup",
        process_HEN_built_or_capex_priced=False,
        baseline_assumes_ideal_process_heat_recovery=True,
        compressor_qualified=False,industrial_validation=False,
        all_inputs_synthetic=True,
        manufacturer_CAPEX_known=False)

"""Finite scenario enumeration / Pareto exposure, not industry equipment optimisation."""
from __future__ import annotations
from dataclasses import dataclass,replace
from math import isfinite
from .integration import ProcessSite,TariffBlock,evaluate_site

@dataclass(frozen=True)
class Sensitivity:
    hp_nameplates_kW:tuple[float,...]=(250.,500.,1000.)
    carnot_fractions:tuple[float,...]=(.35,.45,.55)
    electricity_price_multipliers:tuple[float,...]=(.75,1.,1.25)
    pinch_dt_min_K:tuple[float,...]=(10.,20.)

    def __post_init__(self):
        for name,values in vars(self).items():
            if not values or len(set(values))!=len(values) or not all(
                type(v) in (int,float) and isfinite(v) and v>0 for v in values):
                raise ValueError(f"invalid sensitivity dimension {name}")
        if max(self.carnot_fractions)>1:
            raise ValueError("Carnot fractions may not exceed one")
        count=1
        for dimension in vars(self).values():
            count*=len(dimension)
        if count>2000:
            raise ValueError("scenario budget over 2000; reduce combinatorial exploration")

def _dominates(a:dict,b:dict) -> bool:
    """Matched price, Carnot fraction and process pinch only.

    Three objectives: annual operating saving maximised,
    heat-electrification fraction maximised, compressor nameplate minimised.
    These objectives are NOT CAPEX, investment NPV or CO2 minimisation.
    """
    ea,eb=a["result"],b["result"]
    things=(
      ea["annual_net_savings_eur"] >= eb["annual_net_savings_eur"]-1e-8,
      ea["fraction_external_heating_electrified"] >= eb["fraction_external_heating_electrified"]-1e-10,
      a["hp_nameplate_kW"] <= b["hp_nameplate_kW"]+1e-9)
    strict=(
      ea["annual_net_savings_eur"]>eb["annual_net_savings_eur"]+1e-8,
      ea["fraction_external_heating_electrified"]>eb["fraction_external_heating_electrified"]+1e-10,
      a["hp_nameplate_kW"]<b["hp_nameplate_kW"]-1e-9)
    return all(things) and any(strict)

def enumerate_scenarios(site:ProcessSite, sensitivity:Sensitivity)->dict:
    rows=[]
    idx=0
    for dt in sensitivity.pinch_dt_min_K:
        for eta in sensitivity.carnot_fractions:
            for price_multiplier in sensitivity.electricity_price_multipliers:
                group=[]
                for nameplate in sensitivity.hp_nameplates_kW:
                    blocks=tuple(replace(x,electricity_eur_kWh=x.electricity_eur_kWh*price_multiplier)
                                 for x in site.tariff_blocks)
                    variant=replace(site,tariff_blocks=blocks,hp_nameplate_kW=nameplate,
                                    heat_pump_carnot_fraction=eta,pinch_dt_min_K=dt)
                    result=evaluate_site(variant)
                    idx+=1
                    row=dict(scenario_id=f"{site.site_id}_S{idx:03d}",
                        pinch_dt_min_K=dt,assumed_carnot_fraction=eta,
                        electricity_price_multiplier=price_multiplier,
                        hp_nameplate_kW=nameplate,
                        result=result)
                    group.append(row)
                for row in group:
                    row["non_dominated_within_identical_assumptions"]=not any(
                      _dominates(other,row) for other in group if other is not row)
                rows.extend(group)
    return dict(site_id=site.site_id,scenarios=rows,total_cases=len(rows),
        scenario_enumeration_not_full_HEN_or_dispatch_optimization=True,
        economic_CEILING_not_purchase_quote=True,
        no_probabilistic_interpretation_of_scenario_envelope=True,
        no_cross_scenario_Pareto_comparison=True)

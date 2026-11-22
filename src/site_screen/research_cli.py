"""Strict JSON batch interface for multi-stream industrial integration screening."""
from __future__ import annotations
import argparse
from dataclasses import fields
import json
from pathlib import Path
from .pinch import ProcessStream
from .integration import ProcessSite,Source,TariffBlock,evaluate_site
from .portfolio import Sensitivity,enumerate_scenarios

def _known_only(data,cls,context):
    if not isinstance(data,dict):raise ValueError(f"{context} must be an object")
    legal={f.name for f in fields(cls)}
    unknown=set(data)-legal
    if unknown:raise ValueError(f"{context} contains unknown fields {sorted(unknown)}")
    return data

def read_study(path:str|Path)->tuple[list[ProcessSite],Sensitivity]:
    doc=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(doc,dict) or set(doc)!={"schema_version","data_provenance","sites","sensitivity"}:
        raise ValueError("study schema requires only version, provenance, sites, sensitivity")
    if doc["schema_version"]!="1.0":raise ValueError("schema_version must be 1.0")
    if doc["data_provenance"]!="synthetic":raise ValueError(
        "example v1.0 CLI accepts only explicitly synthetic inputs")
    if not isinstance(doc["sites"],list) or not doc["sites"] or len(doc["sites"])>100:
        raise ValueError("1..100 sites required")
    sites=[]
    identities=set()
    for i,raw in enumerate(doc["sites"]):
        ctx=f"site[{i}]"
        fields_= _known_only(raw,ProcessSite,ctx).copy()
        if not isinstance(fields_.get("streams"),list) or not fields_["streams"]:
            raise ValueError(f"{ctx} requires process streams")
        if not isinstance(fields_.get("tariff_blocks"),list) or not fields_["tariff_blocks"]:
            raise ValueError(f"{ctx} requires tariff blocks")
        fields_["streams"]=tuple(ProcessStream(**_known_only(x,ProcessStream,ctx+".stream"))
                                   for x in fields_["streams"])
        fields_["independent_source"]=Source(**_known_only(fields_["independent_source"],Source,ctx+".source"))
        fields_["tariff_blocks"]=tuple(TariffBlock(**_known_only(x,TariffBlock,ctx+".tariff"))
                                        for x in fields_["tariff_blocks"])
        try:
            site=ProcessSite(**fields_)
        except (ValueError,TypeError) as err:
            raise ValueError(f"{ctx}: {err}") from err
        if site.site_id.casefold() in identities:raise ValueError("duplicate site_id")
        identities.add(site.site_id.casefold());sites.append(site)
    raw=_known_only(doc["sensitivity"],Sensitivity,"sensitivity")
    sens=Sensitivity(**{k:tuple(v) if isinstance(v,list) else v for k,v in raw.items()})
    if len(sites)*len(sens.hp_nameplates_kW)*len(sens.carnot_fractions)*len(
          sens.electricity_price_multipliers)*len(sens.pinch_dt_min_K)>10000:
        raise ValueError("total scenario budget exceeds 10000")
    return sites,sens

def main(argv:list[str]|None=None)->int:
    p=argparse.ArgumentParser(description="Research-grade algebraic industrial HTHP screening, not site design")
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--scenarios",action="store_true",
                   help="enumerate pinned-provenance source, price and nameplate sensitivity")
    a=p.parse_args(argv)
    sites,sens=read_study(a.input)
    cases=[evaluate_site(x) for x in sites]
    report=dict(schema_version="1.0",data_provenance="synthetic",
       tool_class="equation-verified, externally-unvalidated screening",
       site_count=len(sites),cases=cases,
       scenario_matrix=[enumerate_scenarios(x,sens) for x in sites] if a.scenarios else None,
       scientific_limits=[
           "No manufacturer compressor performance map or measured process streams",
           "Constant sensible cp and theoretical maximum pinch process recovery; no heat exchanger network",
           "External waste heat source is declared separately, not process double-counted",
           "COP is assumed fraction of Carnot, not refrigerant/pressure/compressor validated",
           "Tariff blocks dispatch heat pump ON/OFF against boiler with no thermal storage or process ramp",
           "Sources, tariffs and price sensitivity are not probabilities or market forecasts",
           "CAPEX break-even is a ceiling, not a supplier estimate or proven investment NPV",
           "Process energy and equipment hydraulics, true part-load and electricity demand charges missing",
           "No genuine industrial site, experimental holdout or external uncertainty validation"
       ])
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print(f"{len(sites)} synthetic sites; {sum(x['total_cases'] for x in report['scenario_matrix']) if a.scenarios else 0} sensitivity scenarios -> {a.output}")
    return 0

if __name__=="__main__":raise SystemExit(main())

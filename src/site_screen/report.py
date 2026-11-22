"""Readable deterministic research summary for synthetic multi-stream screening."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

def _f(x,decimals=2):return f"{x:,.{decimals}f}"

def render(report:dict)->str:
    if report.get("schema_version")!="1.0" or report.get("data_provenance")!="synthetic":
        raise ValueError("only synthetic v1.0 research evidence can be reported")
    cases=report.get("cases")
    if not isinstance(cases,list) or not cases:
        raise ValueError("empty v1.0 results")
    lines=[
        "# IndustrialHeatPumpSiteScreen — v1.0 synthetic study",
        "",
        "**Research classification:** equation-verified algebraic models and",
        "synthetic scenarios; **no measured industrial or compressor validation**.",
        "",
        "## Site screening results",
        "",
        "| Synthetic site | Process hot utility (kW) | Ideal process recovery (kW) | Heat electrified (%) | Annual net saving (EUR) | Incremental CAPEX break-even ceiling (EUR) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for site in cases:
        p=site["process_heat_cascade"]
        lines.append("| "+site["site_id"]+" | "+
            _f(p["minimum_external_heating_kW"])+" | "+
            _f(p["maximum_internal_process_heat_recovery_kW"])+" | "+
            _f(100*site["fraction_external_heating_electrified"],1)+" | "+
            _f(site["annual_net_savings_eur"],0)+" | "+
            _f(site["break_even_incremental_installed_capex_eur"],0)+" |")
    lines+=["",
        "The **break-even ceiling is not an equipment cost estimate**. Annual",
        "savings refer to the same ideal internally recovered process network",
        "with and without a hypothetical HP retrofit.",
        "",
        "## Assumptions and evidence quality",
        "",
        "- All source/demand measurements, prices, component capacities and production profiles are synthetic.",
        "- The process pinch method calculates energy targets, not implementable exchanger matches or plant retrofit costs.",
        "- HP source heat is independent of internally recovered process heat, avoiding double-counting.",
        "- COP comes from an assumed Carnot fraction; no measured refrigerant/compressor map is used.",
        "- Tariff blocks are nonchronological and include a hypothetical boiler fallback, not storage or market dispatch.",
        "- Compressor and fixed/variable auxiliary electricity are included, but equipment hydraulic/heat-loss details are not.",
        "- Heat, source and boiler first-law balances are checked; actual industrial performance is unvalidated.",
        "",
        "## Reproducibility",
        "",
        "`python -m unittest discover -s tests -v`",
        "",
        "`python -m site_screen.research_cli --input data/synthetic_process_sites.json --output results/v1_process_screen.json --scenarios`",
        "",
        "The full JSON contains all source-heat balances, tariff decisions and",
        "model-only assumptions. The scenario envelopes are *not probabilities*.",
        ""
    ]
    return "\n".join(lines)

def main(argv:list[str]|None=None)->int:
    a=argparse.ArgumentParser()
    a.add_argument("--input",type=Path,required=True)
    a.add_argument("--output",type=Path,required=True)
    x=a.parse_args(argv)
    data=json.loads(x.input.read_text(encoding="utf-8"))
    text=render(data)
    x.output.parent.mkdir(parents=True,exist_ok=True)
    x.output.write_text(text,encoding="utf-8")
    print(f"Research summary: {x.output}")
    return 0

if __name__=="__main__":raise SystemExit(main())

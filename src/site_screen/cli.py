"""Batch CLI for preliminary industrial HTHP site screening."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from .io import load_sites
from .model import screen_site

SCHEMA_VERSION = "0.1"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preliminary industrial HTHP site screen")
    parser.add_argument("csv_path", type=Path, help="Site input CSV")
    parser.add_argument("--output", type=Path, required=True, help="Deterministic JSON results")
    a = parser.parse_args(argv)
    sites = load_sites(a.csv_path)
    results = [screen_site(site) for site in sites]
    report = dict(
        schema_version=SCHEMA_VERSION,
        study_type="synthetic research screening, not industrial validation",
        input_site_count=len(sites),
        results=results,
        highest_positive_break_even_sites=[
            r["site_id"] for r in sorted(results,
                key=lambda x: x.get("pv_net_savings_before_capex_eur", float("-inf")),
                reverse=True)
            if r.get("positive_economic_break_even_ceiling", False)
        ],
        exclusions=[
            "No real industrial site data or equipment qualification",
            "COP is a user-assumed Carnot fraction, not natural-fluid EOS or measured compressor map",
            "No site-level heat integration or composite-curve pinch analysis",
            "No part-load COP, hourly electricity dispatch, tariff charges or annual degradation",
            "No refrigerant piping, process/waste-heat exchanger sizing, pumps or compressor auxiliaries",
            "No manufacturer CAPEX; maximum supported CAPEX is an economic threshold, not a price",
        ],
    )
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Screened {len(results)} sites -> {a.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

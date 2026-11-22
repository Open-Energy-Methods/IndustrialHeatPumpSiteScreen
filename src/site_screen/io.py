"""Strict, deterministic CSV ingestion with explicit row provenance."""
from __future__ import annotations
import csv
from dataclasses import fields
from pathlib import Path
from .model import Site

_FIELDS = {field.name: field for field in fields(Site)}
# Required columns are defined explicitly for a stable CSV input contract.
REQUIRED = (
    "site_id", "source_supply_C", "source_return_C",
    "source_flow_kg_s", "process_return_C", "process_supply_C",
    "process_demand_kW", "operating_hours_per_year",
    "electricity_eur_per_kWh", "boiler_fuel_eur_per_kWh", "boiler_efficiency"
)


def load_sites(path: str | Path) -> list[Site]:
    result: list[Site] = []
    seen: set[str] = set()
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError("CSV must include a header")
        unexpected = set(reader.fieldnames) - set(_FIELDS)
        missing = set(REQUIRED) - set(reader.fieldnames)
        if unexpected or missing:
            raise ValueError(f"Invalid columns: unexpected={sorted(unexpected)}, missing={sorted(missing)}")
        for line, row in enumerate(reader, start=2):
            if any(k is None for k in row) or any(v is None for v in row.values()):
                raise ValueError(f"Line {line}: malformed CSV row")
            args: dict = {"site_id": (row["site_id"] or "").strip()}
            for field_name in _FIELDS:
                if field_name == "site_id" or field_name not in row:
                    continue
                val = (row[field_name] or "").strip()
                if not val:
                    if field_name in REQUIRED:
                        raise ValueError(f"Line {line}: missing {field_name}")
                    continue
                try:
                    args[field_name] = int(val) if field_name == "lifetime_years" else float(val)
                except ValueError as exc:
                    raise ValueError(f"Line {line}: invalid numeric {field_name}: {val!r}") from exc
            try:
                site = Site(**args)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Line {line}: {exc}") from exc
            identity = site.site_id.casefold()
            if identity in seen:
                raise ValueError(f"Line {line}: duplicate site_id {site.site_id!r}")
            seen.add(identity)
            result.append(site)
    if not result:
        raise ValueError("No site rows found")
    return result

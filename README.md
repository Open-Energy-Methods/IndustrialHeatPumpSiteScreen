# IndustrialHeatPumpSiteScreen

**Version 1.0.0 — reproducible, synthetic industrial heat-integration research prototype.**

[![CI](https://github.com/Open-Energy-Methods/IndustrialHeatPumpSiteScreen/actions/workflows/v1-methodological.yml/badge.svg)](https://github.com/Open-Energy-Methods/IndustrialHeatPumpSiteScreen/actions/workflows/v1-methodological.yml)

**Scientific status:** Verified software arithmetic and analytical limiting cases; **not** validated industrial energy performance, equipment design, actual economic viability, or a qualified compressor map.

This is a separate research work sample oriented toward the **DTU Construct HeatMinds PhD on industrial integration of high-temperature heat pumps (job 8486)**. [CarnotBatteryLab](https://github.com/Open-Energy-Methods/CarnotBatteryLab) instead studies thermodynamic architecture and thermal storage, relevant to job 8487. This work is **independent** and does not imply DTU affiliation, endorsement or sponsorship.

## What v1.0 actually computes

1. **Multi-stream process heat recovery:** Classical shifted-temperature / problem-table pinch analysis. It reports ideal minimum hot and cold utilities and recoverable process heat for an assumed ΔTmin; it does not design the exchanger network.
2. **Separated heat-pump source:** The HP evaporator's waste-heat source is explicit and independent from the hot streams already credited to process-to-process heat recovery.
3. **Site-level conditional heat-pump integration:** Carnot-fraction COP proxy and source heat, nameplate, process supply-temperature, boiler-backup and first-law constraints.
4. **Price-aware operation:** Deterministic ON/OFF dispatch in independent annual tariff blocks, with compressor and assumed auxiliary electricity and a boiler supplying all residual heat. No chronological storage, process ramps or equipment turndown models.
5. **Economic threshold:** Annual fuel displaced, electricity cost, discounted operating savings and *maximum incremental installed CAPEX supported*. This is **not** a supplier quote or proof of investment profitability.
6. **Scenario sensitivity:** Full-factorial enumerations of theoretical COP fraction, HP nameplate, electricity prices and process ΔTmin. Non-dominated capacities are evaluated only under matched price/efficiency/pinch conditions; not a probability distribution or a whole-site co-optimisation.

**Never describe this code as a measured R718/R600/R600a model.** It deliberately does not import CarnotBatteryLab's preliminary working-fluid cycle calculations. External measurements, independent compressor holdouts and actual process data are required for equipment conclusions.

## Reproduce

Python 3.11+ (stdlib only):

```bash
python -m pip install -e .
python -m unittest discover -s tests -v

# Legacy v0.1 single-stream CSV screen (backward compatible)
python -m site_screen.cli data/synthetic_sites.csv --output results/legacy.json

# v1.0 multi-stream process, economics and tariff sensitivity
python -m site_screen.research_cli \
  --input data/synthetic_process_sites.json \
  --output results/v1_process_screen.json \
  --scenarios

# Human-readable research report accompanying reproducible JSON
python -m site_screen.report \
  --input results/v1_process_screen.json \
  --output results/v1_research_summary.md
```

The v1.0 fixture contains three explicitly **synthetic** sites with independent waste-heat streams and 162 predeclared scenario combinations. CI tests both Python 3.11 and 3.12, validates first-law/process balances, retains rejection cases and checks JSON byte-for-byte determinism.

## Output interpretation

- `minimum_external_heating_kW`: theoretical pinch utility after *ideal* internal heat recovery.
- `maximum_internal_process_heat_recovery_kW`: process hot-to-cold transfer target, not installed exchanger performance.
- `independent_source`: waste heat excluded from internal process recovery so it cannot be double counted.
- `assumed_COP`: heuristic fractional-Carnot screen, not compressor-map prediction.
- `hp_delivered_kW`, `hp_compressor_electric_kW`, `boiler_remaining_kW`: conditional heating service, with balanced source energy.
- `annual_net_savings_eur`: scenario-specific incremental operating savings relative to the *same ideal recovery network*.
- `break_even_incremental_installed_capex_eur`: PV ceiling for an unknown investment cost, not observed market price.
- `non_dominated_within_identical_assumptions`: multi-criterion scenario screening among nameplate choices only.

## Scientific documentation

- [Methods, boundary conditions and literature](docs/v1_methods.md)
- [Release evidence and unvalidated gates](docs/v1_release_checklist.md)
- [Independent site/equipment validation plan](docs/validation_plan.md)
- [Further research milestones](https://github.com/Open-Energy-Methods/IndustrialHeatPumpSiteScreen/issues/2)
- [Synthetic source data](data/synthetic_process_sites.json)

The program has a deliberately narrow **software-v1.0** definition. A validated industrial screening tool would require process stream measurements, uncertainties, compressor envelopes and controlled experiments. Green CI alone does not confer that validity.

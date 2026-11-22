# IndustrialHeatPumpSiteScreen

A research-oriented, **preliminary industrial-site screening tool** for high-temperature heat-pump integration.

**Status:** v0.1 research prototype under development. No field measurements, validated compressor map, vendor quotation, process-integration optimisation or industrial certification are claimed.

The project addresses a different question from [CarnotBatteryLab](https://github.com/Open-Energy-Methods/CarnotBatteryLab): **At which industrial sites could a high-temperature heat pump be thermodynamically and economically worth investigating?** The present screen is not a verified site-design tool.

## Research scope
- Reproducible batch screening of synthetic industrial sites with heat-source and heat-demand constraints.
- Transparent, bounded Carnot-fraction **COP proxy** (not a fluid-specific performance map).
- Heating duty, heat recovered, compressor electricity, residual boiler fuel.
- Conditional annual net savings and installed-CAPEX break-even ceiling.
- Explicit feasibility/rejection reasons and reproducible tests.

Future work may add validated R600/R600a or R718 compressor data, process pinch analysis, site uncertainty distributions, dispatch optimisation, equipment pricing and independent experimental validation. None of these are implemented in v0.1.

## Reproducibility
Use Python 3.11+ and install locally with `python -m pip install -e .`. Run
`python -m unittest discover -s tests -v` and
`python -m site_screen.cli data/synthetic_sites.csv --output results/synthetic_screen.json`.

**All distributed sites are synthetic.** See [method and assumptions](docs/methodology.md) and [validation plan](docs/validation_plan.md).

## Research context
Built independently as a portfolio research prototype relevant to **DTU Construct, HeatMinds PhD job 8486** (industrial HTHP integration), not as an institutionally approved DTU project or demonstration of industrial performance.

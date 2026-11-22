# Verification and scientific validation plan — v1.0.0

## Definition of scope

The v1.0 package is a **stable mathematical research-software release**.
Analytical unit tests, numerical first-law balances and strict synthetic
provenance demonstrate implementation consistency. They are not external
scientific validation against industrial measurements.

| Gate | Evidence in v1.0 | Classification |
|---|---|---|
| Algebraic thermal COP first law | Qheat = Qwaste + W; boiler closes remaining heat | Unit and CI equations verified |
| Multi-stream process heat recovery | Shifted-temperature interval cascade; no negative utility | Analytical limits and numerical conservation verified |
| Independent waste source | External HP source separate from recovered process hot streams | Schema and regression verified |
| Tariff-block economics | Boiler displaced + compressor/aux electricity + fixed OPEX | Unit and sensitivity verified |
| Energy service | Tariff blocks enforce Qutility = QHP + Qboiler | Conservation verified |
| Discount break-even | Fixed annual savings and independent PV annuity | Algebraic verification |
| Scenario comparison | Full-factorial variations with within-hypothesis dominance | Deterministic synthetic verification |
| Reproducibility | Python 3.11/3.12, deterministic JSON replay | GitHub Actions |
| Natural-fluid compressor data | No calibrated R600/R600a/R718 map or independent holdout | **Not validated** |
| Site process stream measurements | Synthetic temperature, demand and waste-source data only | **Not validated** |
| Heat exchanger design | No HEN matching, area, hydraulics or installation | **Not implemented** |
| Equipment capital cost | No manufacturer quotation | **Unknown** |
| Market flexibility | Independent price blocks; no chronological TES or operating ramp | **Not validated** |
| Multi-objective optimisation | Discrete capacity screening, not joint plant network synthesis | **Not implemented** |

## Required next research tasks before industrial conclusions

1. Obtain industrial source/sink measurement provenance, calorimetric
   uncertainty, real hourly availability and independent site holdouts.
2. Model physical HP temperature glide and local HX pinch conditions with a
   manufacturer compressor map including discharge-T, speed and pressure limits.
3. Verify process HEN matching and retrofit utility baselines, including
   equipment area, installed exchanger and pipe costs and water pumping.
4. Compare against independent plant-metered fuel/heat/electricity and audited
   equipment quotes; propagate uncertainties and report falsifying examples.
5. Develop process-consistent chronological dispatch, TES and demand-response
   modelling with production constraints; test generalisation out-of-sample.

**No official or externally certified industrial v1.0 validation is claimed.**

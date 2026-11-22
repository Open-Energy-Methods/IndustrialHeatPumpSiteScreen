# v1.0 software release gates (scientific validation explicitly excluded)

| Gate | Requirement | Evidence source |
|---|---|---|
| Schema | Strict site, stream, independent source, tariff block; only synthetic release dataset | `tests/test_research_cli.py` |
| Pinch targeting | Interval heat cascade, ≥0 utilities, exactly conserved source/cold loads | `tests/test_pinch.py` |
| HP first law | Qheat = Qexternal waste + Wcompressor; no duplicate process recovery | `tests/test_integration.py` |
| Heating service | Qprocess,pinch = QHP + Qboiler, all tariff blocks | `tests/test_integration.py` |
| Electricity | Compressor, proportionate and fixed-active auxiliaries | `tests/test_integration.py` |
| Economics | Independent annual fuel/electricity/discount accounting | `tests/test_model.py`, `tests/test_integration.py` |
| Scenario integrity | Full factorial deterministic cases, Pareto only under matched counterfactual | `tests/test_portfolio.py` |
| Input failures | Unphysical temperatures, invalid hours, malformed field names, non-synthetic data | `tests/test_research_cli.py` |
| Reproduction | Python 3.11 and 3.12, byte-for-byte CLI JSON replay, first-law audit | GitHub Actions `v1.0 process integration and evidence audit` |
| Methods | Source-checked scientific identity, limitations, assumptions and supported claims | `docs/v1_methods.md` |
| Packaging | stdlib-only pip editable install, stable CLI, semver `1.0.0` | `pyproject.toml` |

**Meaning of v1.0:** the *screening software API and reproducible synthetic verification* are stable.
It is **not** a completed validated industrial HTHP integration model, optimisation platform,
refrigerant compressor map, industrial investment recommendation or certified device.

### Deferred (not optional before any industrial viability claim)
- Real-site process measurements, measurement uncertainty, time variation and
  independent holdout cases.
- Refrigerant- and compressor-specific measured performance envelopes, turndown,
  temperature limits, discharge pressure, maintenance and auxiliaries.
- Actual process network synthesis, pinch feasibility including heat-exchanger area,
  thermal buffering and pressure drops.
- Manufacturer quotations, installation prices and site-specific economic and
  environmental sensitivity.
- Chronological price-driven heat-pump/boiler/thermal store dispatch, real
  constraints and actual market participation.

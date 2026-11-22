# Methodology and assumptions — v0.1

**Scope:** deterministic, reproducible screening across hypothetical industrial sites. There is no industrial site validation, experimental compressor map, vendor CAPEX, process integration heat cascade, TES, hourly power dispatch or site-specific optimised heat recovery.

## Functional unit and input basis
Each site specifies bulk source **inlet / outlet**, source mass flow, process inlet / required outlet, peak heat demand, equivalent annual operating hours, electricity/fuel prices and baseline boiler efficiency. All distributed site records are synthetic; site labels must not be confused with measured industrial records. Heat demand is assumed constant during those hours and residual demand is met by the existing boiler at unchanged efficiency.

## Thermodynamic screen
Source heat bound in kW:

\`Q_source,max = m_source * cp_source * (T_source,in - T_source,out)\`

Assumed pinch-adjusted temperature proxies in kelvin:

\`T_cond = T_process,out + ΔT_hot + 273.15\`
\`T_evap = T_source,out - ΔT_cold + 273.15\`

The ideal heating COP is \`COP_Carnot = T_cond/(T_cond-T_evap)\`, and the **screening proxy** is \`COP = f_assumed * COP_Carnot\`. Here f is an explicitly selected *assumed* fraction, not measured, fitted or valid for all fluids and compressor capacities. Reject when proxy COP≤1, or when temperatures cannot establish a positive lift. The current default f=0.45 and both 5 K approaches are arbitrary illustrative design inputs. They are not claims of an envelope-supported industrial R600, R600a or R718 compressor.

With heat pump output Q_hot, source heat Q_source and compressor electricity W:

\`Q_hot = Q_source + W\`, \`W = Q_hot/COP\`, and \`Q_source = Q_hot*(1-1/COP)\`.

The maximum served duty is \`min(Q_process, Q_source,max/(1-1/COP))\`; any remaining process duty is assumed supplied by the original boiler. No condenser/evaporator distributed pinch, varying heat capacities, ambient losses, temperature-dependent fluid properties, motor drive losses or partial-load limits are resolved. The 80°C-source experiment in CarnotBatteryLab uses a different EOS and boundary, and its COPs are **not inherited as validation**.

## Economic boundary
Annual displaced boiler-fuel consumption = served heat (kW) × annual hours / existing boiler efficiency. Annual HP electricity = served heat / assumed COP × hours. Incremental fixed OPEX is an explicit annual input; all HP auxiliary electricity and other operating expenditures are not yet included. Annual pre-CAPEX savings:

\`S = displaced fuel cost - HP compressor electricity cost - incremental fixed OPEX\`.

For end-of-year savings over N years, discount factor r, the economic break-even installed-CAPEX threshold is \`C_BE = max(0, sum(S/(1+r)^y, y=1..N))\`. A negative pre-CAPEX present value is reported *separately*; zero displayed break-even CAPEX does not conceal the negative operating economics. Electricity and fuel prices are constant synthetic values; real investment cost is **unknown**, not zero. No carbon prices, taxes, grid demand charges, replacement cost, water permits, subsidies, or equipment degradation. The constant-price tariff threshold for break-even operating expenditure is computed independently.

## Interpretation
Output status \`full_heat_demand_proxy\` means only that the stylized first-law screen supplies all heat demand with source flow and assumed COP. \`source_limited_proxy\` means only part of process duty is served. \`rejected\` preserves the negative feasibility result. No label implies hardware, process, economic purchase-price or industrial integration validation. Ranking by threshold is *not* optimisation of site utility systems or demonstration of flexible market participation.

## Reproduction and falsification
\`python -m unittest discover -s tests -v\` checks first-law identity, source limitation, annual boiler-fuel displacement, discounted break-even, no-savings tariffs, explicit rejection, strict CSV schema and deterministic serialization. Two independent Python versions are checked in GitHub Actions. Tests verify implemented equations and do not substitute for experimental or site-record validation.

## Next evidence gates
1. Source/procurement rights and traceability of anonymised industrial site streams, operating-hour profiles and heat supply requirements.
2. Independent refrigerant EOS and measured compressor performance across pressures, discharge temperatures, flow rates and speed; no R718/R600 qualification currently exists.
3. Variable-temperature process integration via composite curves or temperature-interval MILP; thermodynamically consistent source heat availability and required exchanger area.
4. Auxiliary and installed equipment CAPEX/OPEX models with validated supplier assumptions and independent economic benchmarks.
5. Time-series demand, electricity prices and flexibility/thermal storage dispatch, including out-of-sample validation.

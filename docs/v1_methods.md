# IndustrialHeatPumpSiteScreen v1.0 — independently testable methodology

**Classification:** v1.0 software API / mathematical-screening release; **NOT**
v1.0 experimental validation, process-plant qualification, or manufacturer
heat-pump selection. All supplied inputs are synthetic.

## Why this is separate from CarnotBatteryLab

CarnotBatteryLab studies transient energy storage, HTHP charging and packed-bed
architectures. IndustrialHeatPumpSiteScreen instead asks which site
conditions *might merit detailed industrial integration study*. It does
not inherit or import any compressor map from CarnotBatteryLab.

## Stream-by-stream process thermal targeting

Process streams have direction (hot cooling, cold heating), supply and target
temperatures [°C], and constant heat-capacity flow rate C [kW/K]. Every hot
stream is shifted DOWN by ΔTmin/2, every cold stream UP by ΔTmin/2. For
temperature intervals descending from T_i to T_(i+1),

    ΔH_i = (Σ C_hot,i − Σ C_cold,i) (T_i − T_(i+1)).

Cascade from zero, then add the minimum hot utility sufficient to make all
cumulative residuals nonnegative. Residual at the bottom is minimum cold
utility. Maximum recoverable internal heat is Q_cold,total − Q_hot,min, and must
also equal Q_hot,total − Q_cold,min. Regression tests cover no hot streams,
complete recovery, impossible temperature overlap, multiple streams and
monotonic impact of increasing ΔTmin. This is the classical *pinch energy
target*, **not** physical heat exchanger matching, installed recovery
equipment or valid process operability.

The heat pump's evaporator source is specified **independently** from the
internally recovered hot streams. Reusing the same waste heat in both would
double count recovered heat and invalidate the result. Remaining process heat
is an *ideal pinch-target utility*, not necessarily measured existing boiler
load. An industrial baseline must later establish whether its process recovery
network already exists and the relevant incremental HEN costs.

## COP surrogate and source/sink necessary constraints

Use the highest process cold target as a conservative proxy for heat-pump
sink temperature. Condensing proxy = max cold target + ΔT_hot; evaporating
proxy = independently declared external source RETURN − ΔT_cold. Convert
both to kelvin; require positive lift and absolute temperatures. Assumed
COP = f * T_cond/(T_cond−T_evap), with f in (0,1] and default 0.45.
Values of f are hypotheses; this is not a validated efficiency band nor
a universal physics law for all refrigerants.

For rated condenser thermal capacity Qrated and recoverable external
source heat Qsrc, the heat pump's potential heat contribution is

    QHP ≤ min(Q_process_utility, Qrated, Qsrc / (1−1/COP)).

Enforce QHP = Qsrc,used + Wcompressor, Qsrc,used ≤ Qsrc,available
and Qprocess_utility = QHP + Qboiler. No heat can remain unserved
in the present base model: the boiler is always available as backup.
The proxy estimates a possible first-law bound, not a demonstrated
compressor operating point or full temperature-glide pinch.

## Tariff-block operational decision

For each declared annual tariff block with hours, load fraction, source
availability and electricity price, scale all process sensible Cp rates
uniformly. Source availability is an independent factor. On/off decision
is based on whether replacing boiler fuel with maximum heat-pump heat at
the assumed COP saves more than compressor + variable electrical auxiliaries
+ fixed on-state auxiliaries. Since the objective is affine in heat input
when the heat pump runs and the on-state overhead is fixed, choosing between
OFF and maximum capacity minimizes modeled operating cost under these
restricted assumptions.

These blocks are **not chronological**; there is no ramping, part-load
performance, storage, startup wear or time-linked thermodynamic optimization.
An electric-boiler fallback does not exist; residual heat uses the stipulated
fossil-fuel boiler.

## Economic boundary and break-even

Both baseline and HP scenarios inherit the SAME ideal pinch heat-recovery
target and process demand. Boiler displaced annual fuel energy is
QHP/ηboiler times block duration. Electricity energy is compressor plus
explicit variable and fixed-on auxiliary rates; source waste heat is not
electricity, and site waste-heat availability remains assumed.

For site prices and operating hours as supplied, net annual saving before
CAPEX is the sum of avoided fuel cost minus HP electricity charges and
incremental fixed OPEX. For an assumed fixed annual saving S, discount r
and horizon N, the maximum *incremental installed CAPEX* supported is:

    max(0, Σ_(y=1..N) S/(1+r)^y ).

Negative annual saving and negative untruncated present values are
retained alongside the zero economic threshold, not hidden. Prices
(including negative electricity prices) are hypotheses; no forecast or
probability interpretation. There is no real CAPEX estimate, process
HEN installation cost, VAT, carbon tax, income tax, capacity charge,
replacement event, salvage, inflation, or equipment procurement quote.

## Sensitivity / multi-objective exposure

For each site, enumerate specified pinch ΔTmin, HP thermal nameplate,
Carnot-efficiency fraction and electricity price multipliers. Each
combination is a separate hypothetical counterfactual. The tool
indicates non-dominated capacities within the **same** price, assumed
efficiency and pinch network on three axes: more annual operating
savings, more process utility heat electrified, and less nameplate.
This is **not** joint process/HP network synthesis, economically
optimized CAPEX or ML-based viability classification. Scenario ranges
are not quantified uncertainty or empirical prediction intervals.

## Scientific pedigree / exact bibliographic identifiers

- Linnhoff, B., and Hindmarsh, E. (1983). The pinch design method for
  heat exchanger networks. *Chemical Engineering Science* 38(5), 745–763.
  DOI: 10.1016/0009-2509(83)80185-7.
- Schlosser, F., Arpagaus, C., and Walmsley, T. G. (2019).
  Heat Pump Integration by Pinch Analysis for Industrial Applications:
  A Review. *Chemical Engineering Transactions* 76, 7–12.
  DOI: 10.3303/CET1976002.
- Schlosser, F., Jesper, M., Vogelsang, J., Walmsley, T. G.,
  Arpagaus, C., and Hesselbach, J. (2020). Large-scale heat pumps:
  Applications, performance, economic feasibility and industrial
  integration. *Renewable and Sustainable Energy Reviews* 133, 110219.
  DOI: 10.1016/j.rser.2020.110219.

The literature motivates research questions and simplified physics;
none of these references validates the synthetic test points or the
particular Carnot-fraction assumptions used here.

## Reproduction and release gates

- `python -m pip install -e .`
- `python -m unittest discover -s tests -v`
- `python -m site_screen.research_cli --input data/synthetic_process_sites.json --output results/v1_process_screen.json --scenarios`
- CI on Python 3.11 and 3.12 reruns the entire study byte-for-byte,
  verifies each site and all 162 parameter scenarios, and uploads the
  JSON artifact.
- Full legacy v0.1 CLI is maintained and independently tested.

## Industrial-scientific validation still blocked

We require process stream measurements and calorimetric uncertainties,
source-availability profiles, site pricing and capital quotations,
qualified operating maps for each natural refrigerant compressor, and
cross-validated process heat-exchanger networks with constraints.
Until then, do not cite this tool as evidence of industrial feasibility,
measured COP, certified ROI, true multi-objective site optimisation,
actual electric-grid flexibility, or published validation.

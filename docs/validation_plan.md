# Validation and release criteria

**Current release class:** model/equation verification only. No external experimental validation.

| Gate | Evidence in v0.1 | Outcome |
|---|---|---|
| Mass/energy conservation of algebraic heat pump | Exact first-law identity and limiting cases | Automated unit tests |
| Source flow and process heat conservation | Thermal maximum and residual boiler duties | Automated unit tests |
| Cost accounting and discounting | Annual fuel/electric boundary and independently derived annuity | Automated unit tests |
| Invalid inputs, duplicate identities and malformed CSV | Fail-closed CSV parser | Automated unit tests |
| Reproducibility | Fixed synthetic CSV and deterministic JSON | Automated CI |
| Real process stream integration | No heat cascade or exchanger-area data | **Not validated** |
| Compressor COP, R600/R600a/R718 hardware | No independently measured map | **Not validated** |
| Market-price flexibility | No chronological dispatch or controls | **Not implemented** |
| Investment viability | No vendor quotations or equipment installed cost | **Not demonstrated** |

A future scientific v1.0 must provide more than green tests: observed site operating points, documented measurement uncertainty, a genuinely independent validation set, qualified compressor performance envelopes, native process heat-recovery analysis and explicit uncertainty/sensitivity in economics.

Do **not** equate a thermodynamic COP proxy with measured equipment performance or a positive CAPEX threshold with a positive net-present value for an actual purchase.

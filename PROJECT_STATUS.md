# Project Status

## Current phase
**Phase 5 — validated model selection and investigator-product hardening**

### Complete
- Dataset: Elliptic2.
- Decision framing: investigator prioritization under constrained review capacity.
- Official five-file release schema verified locally.
- Verified release scale:
  - 49,299,864 background nodes;
  - 196,215,606 background edges;
  - 121,810 labeled connected components;
  - 444,521 labeled nodes;
  - 367,137 labeled edges.
- Verified labels: 119,047 `licit` and 2,763 `suspicious` components.
- Labeled-universe integrity: zero missing endpoints and zero cross-component edges.
- Structural feature store: 19 complete features, zero nulls.
- Structural benchmark:
  - logistic regression PR-AUC 0.026323 / ROC-AUC 0.545966;
  - random forest PR-AUC 0.024107 / ROC-AUC 0.512885.
- Background-node enrichment:
  - exact one-to-one match for all 444,521 labeled nodes;
  - 43 source node features aggregated into 172 component-level features;
  - all 121,810 components retained.
- Validated node-enriched random forest:
  - five-seed PR-AUC mean 0.527917, SD 0.008117;
  - ROC-AUC mean 0.927790;
  - Brier mean 0.015044;
  - top-0.5% precision mean 94.26%, lift mean 41.53x, suspicious captured mean 115.0;
  - top-1% suspicious captured mean 188.8;
  - top-2% suspicious captured mean 261.8;
  - shuffled-label PR-AUC 0.020978 / ROC-AUC 0.486122 against 0.022699 prevalence;
  - stability, permutation, schema-leakage, and feature-dominance gates passed.
- Background-edge enrichment:
  - exact one-to-one match for all 367,137 labeled edges against the 196.2M-row background table;
  - 95 source edge features aggregated into 380 component-level features;
  - all 121,810 components retained with zero null edge aggregates.
- Five-seed node+edge validation:
  - random forest PR-AUC mean 0.502180, SD 0.017084;
  - ROC-AUC mean 0.924748;
  - Brier mean 0.015671;
  - edge enrichment does not improve the winning random forest.
- Final model selection:
  - **preferred model: node-enriched random forest**;
  - node+edge mean PR-AUC is ~4.9% lower and less stable;
  - node-only matches the edge model at the 0.5% review budget and performs better from 1% through 10%;
  - the edge stage is retained as a validated negative incremental-value finding.
- Held-out calibration validation completed on a 60/20/20 train/calibration/test split:
  - raw RF: PR-AUC 0.507435, Brier 0.015337, log loss 0.072548, ECE 0.008812;
  - sigmoid: PR-AUC 0.507435, Brier 0.015334, log loss 0.068664, ECE 0.002716;
  - isotonic: PR-AUC 0.481282, Brier 0.015155, log loss 0.065206, ECE 0.001389.
- Calibration decision:
  - **raw RF score remains the investigator ranking signal**;
  - sigmoid may be used only as an optional calibrated research estimate because it improves ECE/log loss without changing ranking or constrained-review capture;
  - isotonic is not selected operationally because it degrades PR-AUC and top-budget capture despite better calibration metrics.
- Investigator queue semantics hardened:
  - raw-score thresholds such as `0.90 = critical` removed;
  - queue now uses capacity-based priority tiers: top 0.5%, 1%, 2%, 5%, 10%, then standard;
  - queue explicitly marks the model output as `ranking_score_not_probability`.
- Visualization standard corrected and locked:
  - **interactive Plotly 3D is the default for all 3D project visuals**;
  - Seaborn supplies statistical styling / palettes where useful;
  - Matplotlib `mplot3d` is no longer the primary 3D renderer;
  - generated interactive visuals are written as browser-ready `.html` files.

### Current operational interpretation
- Structural features alone carry little useful AML prioritization signal.
- Node-derived features provide the dominant validated signal.
- Edge-derived aggregates add major engineering cost without improving the strongest model.
- Ranking quality matters more than probability calibration for the primary investigator-queue use case.
- Raw scores must not be described as literal suspicious-activity probabilities.
- Scores prioritize human review only; they do not establish criminal activity, make legal determinations, or automate regulatory reporting.

### Next
- Regenerate the preferred node-only investigator queue with capacity-based priority tiers.
- Generate final interactive Plotly 3D model-selection and calibration visuals.
- Replace placeholder investigator reason text with evidence-based, case-specific explanation outputs that do not over-interpret anonymized source features.
- Add a concise validated model-selection / workload narrative to the README and portfolio case study.
- Add a graph-native GLASS-style or equivalent benchmark when compute permits, clearly separated from the feature-engineered baseline.

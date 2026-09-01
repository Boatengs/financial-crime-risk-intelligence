# Project Status

## Current phase
**Phase 3 — validated node-enriched benchmark / final feature-dominance gate**

### Complete
- Dataset selection: Elliptic2.
- Decision framing: investigator prioritization under review constraints.
- Repository architecture pushed to `main`.
- Synthetic smoke-test fixture.
- Baseline modeling and review-budget evaluation code.
- Data-source and licensing register.
- Local smoke test: unit tests and fixture pipeline pass.
- GitHub Actions CI: unit tests and end-to-end fixture pipeline pass.
- Official five-file layout verified against MITIBMxGraph/Elliptic2.
- Local schema profiling completed on the official downloaded release.
- Verified local row counts:
  - 49,299,864 background nodes.
  - 196,215,606 background edges.
  - 121,810 labeled connected components.
  - 444,521 labeled nodes.
  - 367,137 labeled edges.
- Verified feature layout: 43 anonymized node features and 95 anonymized edge features.
- Exact identifiers locked in config: `ccId`, `ccLabel`, `clId`, `clId1`, `clId2`, `txId`.
- Actual downloaded labels verified: 119,047 `licit` components and 2,763 `suspicious` components.
- Labeled-universe integrity verified: zero missing source nodes, zero missing target nodes, and zero cross-component edges.
- Structural feature store built from all 121,810 labeled components with 19 complete structural features and zero nulls.
- Structural benchmark completed:
  - logistic regression PR-AUC 0.026323 / ROC-AUC 0.545966;
  - random forest PR-AUC 0.024107 / ROC-AUC 0.512885;
  - logistic regression top-0.5% lift 1.8055x (5 suspicious components in 122 reviews).
- Background-node enrichment completed successfully:
  - all 444,521 labeled nodes matched exactly once to the 49.3M-row background-node table;
  - zero missing labeled nodes and zero duplicate background matches;
  - 43 node features aggregated by mean, population standard deviation, minimum, and maximum;
  - 172 component-level node-derived features created;
  - all 121,810 components retained, including all 2,763 suspicious components.
- Initial node-enriched benchmark completed:
  - logistic regression PR-AUC 0.145578 / ROC-AUC 0.882008;
  - random forest PR-AUC 0.530556 / ROC-AUC 0.926611;
  - random forest top-0.5%: 117 suspicious components in 122 reviews, 95.90% precision, 21.16% recall, 42.25x lift.
- Five-seed repeated-split validation completed:
  - random forest PR-AUC mean 0.527917, SD 0.008117, range 0.519036–0.539170;
  - random forest ROC-AUC mean 0.927790, SD 0.004619, range 0.922011–0.934841;
  - random forest Brier score mean 0.015044.
- Repeated review-budget stability verified for random forest:
  - top 0.5% precision mean 94.26%, recall mean 20.80%, lift mean 41.53x, suspicious captured mean 115.0 (range 112–117);
  - top 1% precision mean 77.38%, recall mean 34.14%, lift mean 34.09x, suspicious captured mean 188.8 (range 182–194);
  - top 2% precision mean 53.65%, recall mean 47.34%, lift mean 23.63x;
  - top 5% precision mean 29.17%, recall mean 64.30%, lift mean 12.85x;
  - top 10% precision mean 17.42%, recall mean 76.78%, lift mean 7.68x.
- Shuffled-label sanity check passed:
  - logistic regression PR-AUC 0.024480 / ROC-AUC 0.499009;
  - random forest PR-AUC 0.020978 / ROC-AUC 0.486122;
  - both collapse toward the 0.022699 test prevalence / chance discrimination.
- Compact validation-gate summarizer added at `src/summarize_node_validation.py` to surface schema leakage checks, top feature importance, and class-separation evidence without rerunning models.
- Investigator queue selection defaults to the model with the best average precision.
- 3D visualization remains the project standard.

### Next
- Run `src/summarize_node_validation.py` against the existing validation outputs and inspect `validation_gate_summary.json`.
- Confirm no obvious target-name / duplicate-ID / non-finite leakage flags.
- Review top random-forest features and largest standardized class-separation features for excessive dominance; because Elliptic2 features are anonymized, this remains a human-review gate rather than an automatic semantic-leakage verdict.
- Review calibration tables before presenting raw random-forest scores as probabilities.
- If the final gate is clean, proceed to the 95 background-edge feature aggregates in a resource-controlled experiment over the 196.2M-edge table.
- Compare edge-enriched results against the validated node-enriched benchmark and published graph-model references.
- Add graph-native GLASS-style or equivalent benchmark when compute permits.
- Produce portfolio-ready findings and 3D visuals only from verified, validated real-data outputs.
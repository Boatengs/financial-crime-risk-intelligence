# Graph-Native Benchmark

## Purpose

This benchmark tests whether explicit graph message passing adds decision value beyond the validated node-enriched random forest used for investigator prioritization.

The comparison is intentionally internal and fair: seed 42 uses the same 80/20 component split as the existing node-enriched random forest. The graph benchmark uses only the labeled Elliptic2 subgraph universe—444,521 labeled nodes, 367,137 labeled edges, 121,810 labeled components, and the 43 node features. It does **not** use the 196.2M-row background edge graph and is **not** a reproduction of GLASS.

## Data integrity

The graph-native dataset preparation passed all integrity checks:

- 444,521 labeled node rows and 444,521 distinct labeled nodes.
- 444,521 matched node rows; zero missing labeled nodes.
- Zero duplicate background-node matches.
- 43 node features recovered.
- 367,137 labeled edges retained.
- Zero missing source or target nodes.
- Zero cross-component edges.
- 121,810 components retained, including 2,763 suspicious components.
- Zero null component labels.

## Model

The project graph baseline is a directed dual-channel GraphSAGE classifier with:

- separate forward and reverse message-passing channels;
- 43 standardized node features;
- two message-passing layers by default;
- graph-level mean and max pooling;
- class-weighted binary loss;
- an internal validation subset used only to select epoch count;
- retraining on the full 80% training split before one evaluation on the untouched 20% test set.

Seed 42 selected epoch 18 with validation PR-AUC **0.244746**.

## Seed-42 matched-test results

| Model | PR-AUC | ROC-AUC | Base rate |
| --- | ---: | ---: | ---: |
| Node-enriched random forest | 0.530556 | 0.926611 | 0.022699 |
| Directed GraphSAGE | 0.249817 | 0.870199 | 0.022699 |

GraphSAGE PR-AUC is **0.280739 lower**, a **52.9% relative reduction** versus the random forest. ROC-AUC is also lower by **0.056412**.

The GraphSAGE Brier score is **0.138866**. This raw graph-model output is not used as a probability estimate; the primary decision criterion remains ranking and constrained-review performance.

## Investigator-budget comparison

| Review budget | RF captured | GraphSAGE captured | RF precision | GraphSAGE precision | RF lift | GraphSAGE lift |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.5% | 117 | 72 | 95.90% | 59.02% | 42.25x | 26.00x |
| 1% | 190 | 127 | 77.87% | 52.05% | 34.30x | 22.93x |
| 2% | 262 | 168 | 53.69% | 34.43% | 23.65x | 15.17x |
| 5% | 357 | 238 | 29.29% | 19.52% | 12.90x | 8.60x |
| 10% | 421 | 326 | 17.28% | 13.38% | 7.61x | 5.89x |

GraphSAGE captures fewer suspicious components at every review budget. The deficits versus the random forest are:

- top 0.5%: **45 fewer**;
- top 1%: **63 fewer**;
- top 2%: **94 fewer**;
- top 5%: **119 fewer**;
- top 10%: **95 fewer**.

## Decision

**The node-enriched random forest remains the preferred research and investigator-prioritization model.**

The graph-native baseline is retained as a negative-complexity result: within the labeled-subgraph setting and matched seed-42 test set, directed GraphSAGE adds modeling complexity without improving global ranking quality or investigator-budget capture.

A five-seed GraphSAGE validation is not required for current model selection because the seed-42 gap is large across PR-AUC, ROC-AUC, and every operational review budget. Additional graph experiments are therefore research extensions rather than required validation of the current benchmark choice.

## External GLASS reference

The Elliptic2 paper reports GLASS test PR-AUC of approximately 0.208 and ROC-AUC of approximately 0.889 under its published experimental setup. The official preprocessing guide uses the full background graph for GLASS/GNNSeg inputs.

Those published values remain **external reference benchmarks**, not project results. They should not be directly compared to the project GraphSAGE or random-forest metrics because graph scope, split procedure, feature usage, and training setup differ.

## Interpretation rules

- Graph and random-forest scores are prioritization signals, not proof of criminal activity.
- This benchmark supports model selection under constrained review capacity; it does not make legal or regulatory determinations.
- The negative GraphSAGE result is valid evidence that additional model complexity did not create more decision value in this internal setup.
- Published GLASS numbers remain separate until a true full-background-graph reproduction is run.

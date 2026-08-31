# Source Register

## Primary dataset

**Elliptic2 — a large financial-crime-focused graph dataset with labeled subgraphs**  
Kaggle: https://www.kaggle.com/datasets/ellipticco/elliptic2-data-set  
License shown by Kaggle: CC BY-NC-ND 4.0.  
Published scale: 49,299,864 background nodes/clusters; 196,215,606 transaction edges; 121,810 labeled subgraphs; 2,763 suspicious and 119,047 licit.

## Official implementation guide

MITIBMxGraph / Elliptic2  
https://github.com/MITIBMxGraph/Elliptic2

The official guide documents the five files and preprocessing path for GLASS, GNNSeg, and Sub2Vec-style workflows.

## Research paper

Bellei, C. et al. (2024), **The Shape of Money Laundering: Subgraph Representation Learning on the Blockchain with the Elliptic2 Dataset**.  
https://arxiv.org/abs/2404.19109

## Regulatory / operating context

FinCEN, October 9, 2025 — SAR FAQs emphasizing useful prioritization and avoiding low-value noise:  
https://www.fincen.gov/news/news-releases/fincen-issues-frequently-asked-questions-clarify-suspicious-activity-reporting

FFIEC BSA/AML Manual — transaction and surveillance monitoring should be commensurate with risk and use reasonable filtering criteria:  
https://bsaaml.ffiec.gov/manual/AssessingComplianceWithBSARegulatoryRequirements/04

## Secondary benchmark candidate

IBM AML-Data — synthetic banking transactions with laundering labels, useful later for cross-domain validation:  
https://github.com/IBM/AML-Data

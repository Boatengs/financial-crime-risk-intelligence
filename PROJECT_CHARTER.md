# Project Charter

## Project
Financial Crime Risk Intelligence

## Objective
Build a reproducible AML analytics system that prioritizes suspicious transaction subgraphs for human review under constrained investigation capacity.

## Primary benchmark
Elliptic2, a real-world-size Bitcoin transaction graph with labeled licit/suspicious subgraphs.

## Core questions
1. Which subgraphs have the highest estimated laundering risk?
2. Which structural patterns and feature groups drive the alert?
3. How much suspicious activity is captured when investigators can review only the top 0.5%, 1%, 2%, 5%, or 10% of alerts?
4. How do simple, explainable baselines compare with graph-native methods?
5. How stable are rankings under resampling and model changes?

## Non-goals
- Identifying real individuals.
- Generating or submitting regulatory filings.
- Claiming a model score proves criminal conduct.
- Redistributing the Elliptic2 dataset.

## Deliverable standard
The project should be reproducible from source, explicit about assumptions, runnable on a small fixture in CI, and scalable to the official dataset outside CI.

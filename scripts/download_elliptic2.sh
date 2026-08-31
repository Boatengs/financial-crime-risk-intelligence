#!/usr/bin/env bash
set -euo pipefail
mkdir -p data/raw/elliptic2
cat <<'MSG'
Elliptic2 must be obtained from the publisher's Kaggle page and is not redistributed here.
Dataset: https://www.kaggle.com/datasets/ellipticco/elliptic2-data-set

If your Kaggle CLI is authenticated and the dataset terms are accepted, you can run:
  kaggle datasets download -d ellipticco/elliptic2-data-set -p data/raw/elliptic2 --unzip

Then run:
  python run_pipeline.py --raw-dir data/raw/elliptic2
MSG

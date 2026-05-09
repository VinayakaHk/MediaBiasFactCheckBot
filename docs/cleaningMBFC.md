# cleaningMBFC.py

Utility script to normalize URLs in the MBFC dataset.

## Overview

Reads `MBFC.json`, strips trailing slashes from all `url` fields, and writes the cleaned data to `MBFC_modified.json`.

## Usage

```bash
cd docs/
python cleaningMBFC.py
```

## Input/Output

- **Input**: `docs/MBFC.json` — raw Media Bias Fact Check dataset.
- **Output**: `docs/MBFC_modified.json` — cleaned dataset used by the bot at runtime.

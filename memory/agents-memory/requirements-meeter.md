# Requirements Meeter Output

## Zipsafe Decision
- **Result**: false
- **Reason**: Packages with data files — `boto3` contains non-Python data files (`boto3/data/**/*.json`, `boto3/examples/*.rst`) confirmed by filesystem inspection after installation

## CLI Tools
None required.

## Python Dependencies
- `boto3==1.43.108` — Has data files (JSON resource definitions under `boto3/data/`, RST example files under `boto3/examples/`)
- `tabulate==0.10.0` — Pure Python

## Setup.py Changes
- VENDOR_FOLDER added: no (already present in setup.py; logic activates automatically when `vendor/` directory exists and `zip_safe` is False)
- data_files updated: no (existing `zip_safe: False` branch in setup.py already handles vendor bundling)

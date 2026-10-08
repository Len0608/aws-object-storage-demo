# Requirements Meeter Output

## Zipsafe Decision
- **Result**: false
- **Reason**: Packages with data files — boto3/botocore ship non-Python data files (JSON endpoint definitions and service model files) that must be extracted to disk at runtime

## CLI Tools
- None required. Analysis section 6 ("CLI Tool Dependencies") states "No Dependencies."

## Python Dependencies
- boto3==1.43.109 — Has data files (botocore endpoint/service JSON models shipped alongside)
- botocore==1.43.109 — Has data files (JSON endpoint definitions, service models, CA bundle)
- jmespath==1.1.0 — Pure Python (transitive dependency of botocore for response parsing)
- s3transfer==0.19.2 — Pure Python (transitive dependency of boto3 for multipart upload management)
- tabulate==0.10.0 — Pure Python (ASCII table rendering for S3 object listing output)

## Setup.py Changes
- VENDOR_FOLDER added: no (vendor path handling already present; no CLI binaries to vendor)
- data_files updated: no (existing zip_safe: False branch in setup.py already handles dep wheel and optional vendor inclusion)

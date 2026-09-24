# Universal Extension Requirements (Refined)

**Extension Name:** AWS Object Storage Demo
**Original Generated:** 2026-09-24
**Refined:** 2026-09-24
**Agent_id:** Not Specified
**Requirements Completeness:** Moderate Detail
**Target Platform:** Linux

---

# Table of Contents

1. [Overview](#overview)
2. [Actions](#actions)
   - 2.1 [Action 1: List Objects](#21-action-1-list-objects)
   - 2.2 [Action 2: Upload File](#22-action-2-upload-file)
3. [Input Requirements](#input-requirements)
4. [Output Requirements](#output-requirements)
5. [Authentication Requirements](#authentication-requirements)
6. [Environment Variables](#environment-variables)
7. [Operational Behavior](#operational-behavior)
8. [Implementation Notes](#implementation-notes)
9. [Requirements Summary](#requirements-summary)
10. [Document Change History](#document-change-history)
11. [References](#references)

---

# Overview

This document defines the requirements for the AWS Object Storage Demo Universal Extension for Stonebranch Universal Automation Center (UAC).

**Integration Purpose:** Enable UAC tasks to list objects in an AWS S3 bucket and upload local files from the UAC agent Linux host to S3. The extension demonstrates AWS S3 integration with UAC using the boto3 SDK bundled entirely within the extension package, requiring no separate installation on the agent host. This is an MVP/demo integration; the scope is intentionally minimal.

---

# Actions

## 2.1 Action 1: List Objects

**Functional Requirements:**

1. The extension must retrieve objects from the specified S3 bucket.
2. The number of objects retrieved must be capped at the value configured by the `UE_MAX_OUTPUT_RECORDS` environment variable (default: 100).
3. For each object returned, the extension must capture three metadata fields: Key (object name/path), Size (in bytes), and Last Modified (timestamp in ISO 8601 format).
4. The extension must output the object list as a formatted ASCII table to STDOUT using the `rounded_outline` table format, with columns: Key | Size | Last Modified.
5. If the bucket contains more objects than the configured cap, the result must be considered truncated. In that case:
   - STDOUT must include a note: `"Note: Output limited to <cap> records. Total objects in bucket: <total>."`
   - The Extension Output JSON must include `"truncated": true` and `"total_returned": <total>`.
6. If the result is not truncated, the Extension Output JSON must include `"truncated": false` and `"total_returned": <N>`.
7. The Status output field must be set to: `"Success: Listed <N> objects in '<bucket>'"`.
8. The Result output field must be set to: `"<N> objects"`.

## 2.2 Action 2: Upload File

**Functional Requirements:**

1. The extension must upload a specified local file from the UAC agent's Linux filesystem to the specified S3 bucket and S3 object key.
2. On successful upload, the Status output field must be set to: `"Success: Uploaded to s3://<bucket>/<key>"`.
3. On successful upload, the Result output field must be set to the full S3 URI: `"s3://<bucket>/<key>"`.
4. On successful upload, the Extension Output JSON must contain the full S3 URI of the uploaded object.

---

# Input Requirements

## Connection Parameters

- **AWS Credentials** (Credential Field, required): A UAC Credential entity providing AWS authentication. The credential's `user` attribute must contain the AWS Access Key ID; the credential's `password` attribute must contain the AWS Secret Access Key.
  - Example: A UAC Credential named `"AWS-Demo-Credentials"`
  - Applicability: Both actions

- **AWS Region** (Text, required): The AWS region identifier where the target S3 bucket resides.
  - Example: `us-east-1`
  - Applicability: Both actions

## Operation Selection

- **Action** (Choice, required): The S3 operation to perform.
  - Available options:
    - `List Objects` — retrieves and displays objects in the bucket
    - `Upload File` — uploads a local file to the bucket
  - Default presented option: `List Objects`
  - Applicability: Both actions; controls which action-specific fields are shown

## Bucket Parameters

- **Bucket Name** (Text, required): The name of the target S3 bucket.
  - Example: `my-demo-bucket`
  - Applicability: Both actions

## Upload-Specific Parameters

These fields are shown and required only when Action = `Upload File`.

- **Local File** (Text, required when Action = `Upload File`): The full absolute path to the file on the Linux agent host to be uploaded.
  - Example: `/tmp/reports/q3.csv`
  - Applicability: Upload File only

- **S3 Object Key** (Text, required when Action = `Upload File`): The target object key within the S3 bucket. This determines the object's path and name in S3.
  - Example: `reports/q3.csv`
  - Applicability: Upload File only

---

# Output Requirements

## On Success

**Return code:** 0

**Output-only fields** (both must have `defaultListView: true` to appear as columns in the UAC task execution list):

- **Status** (Text, output-only): A brief human-readable result message, always set on completion.
  - List Objects example: `"Success: Listed 42 objects in 'my-demo-bucket'"`
  - Upload File example: `"Success: Uploaded to s3://my-demo-bucket/reports/q3.csv"`

- **Result** (Text, output-only): Action-specific result value.
  - List Objects: Object count — e.g., `"42 objects"`
  - Upload File: Full S3 URI — e.g., `"s3://my-demo-bucket/reports/q3.csv"`

**Extension Output JSON — List Objects (not truncated):**
```json
{
  "result": {
    "objects": [
      {"key": "reports/q3.csv", "size": 12345, "last_modified": "2026-09-24T10:00:00Z"},
      {"key": "data/input.csv", "size": 67890, "last_modified": "2026-09-23T08:30:00Z"}
    ],
    "truncated": false,
    "total_returned": 2
  }
}
```

**Extension Output JSON — List Objects (truncated):**
```json
{
  "result": {
    "objects": [
      {"key": "reports/q3.csv", "size": 12345, "last_modified": "2026-09-24T10:00:00Z"}
    ],
    "truncated": true,
    "total_returned": 2847
  }
}
```

**Extension Output JSON — Upload File:**
```json
{
  "result": {
    "s3_uri": "s3://my-demo-bucket/reports/q3.csv"
  }
}
```

**STDOUT Output — List Objects:**
- A formatted ASCII table using the `rounded_outline` format with columns: Key | Size | Last Modified.
- If truncated, a note line is appended after the table: `"Note: Output limited to 100 records. Total objects in bucket: 2847."`

**STDOUT Output — Upload File:**
- A confirmation message containing the full S3 URI of the successfully uploaded object.

**Success Criteria:**
1. The S3 API call completes without error.
2. The Status output field is populated with the appropriate success message.
3. The Result output field is populated with the appropriate value.
4. The Extension Output JSON is populated with the correct structure for the executed action.
5. Return code is 0.

## On Error

**Return code:** Non-zero (1)

**Status output field:** Set to a descriptive error message identifying the failure.

**Failure Scenarios:**

| Scenario | Description | Root Causes | Status Description Pattern |
|---|---|---|---|
| Authentication Failure | AWS credentials are rejected by S3 | Invalid Access Key ID or Secret Access Key | `"Error: Authentication failed — invalid AWS credentials"` |
| Bucket Not Found | The specified bucket does not exist or is inaccessible | Bucket name typo, wrong region, no access permission | `"Error: Bucket '<bucket>' not found or not accessible"` |
| Local File Not Found | The specified local file path does not exist on the agent host | Incorrect path, file absent at runtime | `"Error: Local file not found: '<path>'"` |
| Permission Denied | The AWS credentials lack the required IAM permissions | IAM policy does not allow the required S3 action | `"Error: Permission denied for operation on '<bucket>'"` |
| Network / Connectivity Error | The agent cannot reach the AWS S3 endpoint | Network outage, DNS failure, proxy misconfiguration | `"Error: Network error — cannot connect to S3"` |

**Input Validation:**
- Required fields must not be empty; validation is required before making any AWS API call.
- Validation error messages must identify which field failed.

---

# Authentication Requirements

AWS credentials are supplied exclusively through a UAC Credential Field. The Credential entity's `user` attribute must contain the AWS Access Key ID and the `password` attribute must contain the AWS Secret Access Key. No other credential supply mechanism (e.g., agent environment variables, instance profiles) is supported by this extension. The extension must use these values to authenticate all S3 API calls explicitly.

---

# Environment Variables

- **UE_MAX_OUTPUT_RECORDS**: Controls the maximum number of S3 objects included in the List Objects STDOUT output and Extension Output JSON. Defaults to `100` if not set. Applies to the List Objects action only.

---

# Operational Behavior

**Dynamic Choice Fields:**
Not applicable — no dynamic choice fields are required.

**Cancel Action:**
Standard UAC task cancellation behavior applies. No special cancel handling is required by the extension.

**Re-run Capability:**
Both actions support re-run. Re-running List Objects re-queries S3 at the time of re-run. Re-running Upload File re-uploads the same local file to the same S3 key, overwriting any existing object at that key.

**Progress Reporting:**
No progress bar is required. STDOUT output written during execution serves as the progress log visible in the UAC task execution detail.

**Dynamic Commands:**
Not applicable — no dynamic commands are required.

---

# Implementation Notes

## Python Compatibility

Python >= 3.11, as configured in the workspace environment.

## Target Platform

Linux x86_64. C extension modules with a confirmed `manylinux_2_17_x86_64` wheel are viable in addition to pure-Python modules. Both `boto3` and `tabulate` are pure-Python, so no binary wheel constraints apply.

## Third-Party Services and Tools

**Amazon S3 (AWS Simple Storage Service)**
- Cloud object storage service used for listing objects and receiving file uploads.
- No specific S3 API version constraint; the boto3 SDK manages API versioning.

**boto3**
- AWS SDK for Python; provides all required S3 operations.
- Version: 1.43.101
- Type: Pure Python
- Must be bundled with the extension. Nothing may be installed separately on the UAC agent host.

**tabulate**
- ASCII table formatting library used for STDOUT output on the List Objects action.
- Version: 0.10.0
- Type: Pure Python
- Must be bundled with the extension.

## Error Handling

**High-level error categories:**
- Authentication errors (invalid or expired AWS credentials)
- Resource errors (bucket not found, local file not found)
- Permission errors (insufficient IAM permissions)
- Network / connectivity errors

**Error handling strategy:** All errors must be caught and result in a descriptive message in the Status output field and a non-zero return code. Unhandled exceptions must not propagate to the UAC agent framework.

**Recovery mechanisms:** None. No automatic retry is required.

## Resource Cleanup

- The extension does not create temporary files and has no persistent connections requiring explicit cleanup.
- All boto3 client objects are ephemeral to the task execution and are released when the task completes.

---

# Requirements Summary

The AWS Object Storage Demo Universal Extension provides two S3 operations — **List Objects** and **Upload File** — using the boto3 SDK bundled within the extension. AWS credentials are managed through a UAC Credential Field (Access Key ID in `user`, Secret Access Key in `password`). The List Objects action retrieves up to `UE_MAX_OUTPUT_RECORDS` (default 100) objects and writes a `rounded_outline` tabulate ASCII table to STDOUT with Key, Size, and Last Modified columns; truncation is reported in STDOUT and in the Extension Output JSON. The Upload File action uploads a local Linux file to a specified S3 bucket and key. Both actions populate two output-only fields — Status and Result — visible as columns in the UAC task execution list. All dependencies (boto3 1.43.101, tabulate 0.10.0) are pure-Python and must be bundled with the extension.

---

# Document Change History

- 2026-09-24: Initial requirements captured — Moderate Detail
- 2026-09-24: Comprehensive refinement based on 5 clarification questions covering module selection (tabulate), authentication design (UAC Credential Field), List Objects metadata fields (Key + Size + Last Modified), output-only fields (Status + Result), and large-output safety net (UE_MAX_OUTPUT_RECORDS cap at 100)

---

# References

- Original Requirements Document: `memory/requirements.md`
- Original Requirements Q&A Document: `memory/agents-memory/requirements-QnA.md`

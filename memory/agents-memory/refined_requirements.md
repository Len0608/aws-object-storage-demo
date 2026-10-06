# Universal Extension Requirements (Refined)

**Extension Name:** AWS Object Storage Demo
**Original Generated:** 2026-10-06
**Refined:** 2026-10-06 03:30:00
**Agent_id:** N/A
**Requirements Completeness:** Moderate Detail
**Target Platform:** Linux

---

# Table of Contents

1. [Overview](#overview)
2. [Actions](#actions)
   - 2.1 [Action 1: List Objects](#action-1-list-objects)
   - 2.2 [Action 2: Upload File](#action-2-upload-file)
3. [Input Requirements](#input-requirements)
   - 3.1 [Connection Parameters](#connection-parameters)
   - 3.2 [Action-Specific Parameters](#action-specific-parameters)
4. [Output Requirements](#output-requirements)
   - 4.1 [On Success](#on-success)
   - 4.2 [On Error](#on-error)
5. [Authentication Requirements](#authentication-requirements)
6. [Environment Variables](#environment-variables)
7. [Operational Behavior](#operational-behavior)
8. [Implementation Notes](#implementation-notes)
   - 8.1 [Python Compatibility](#python-compatibility)
   - 8.2 [Target Platform](#target-platform)
   - 8.3 [Third-Party Services and Tools](#third-party-services-and-tools)
   - 8.4 [Error Handling](#error-handling)
   - 8.5 [Resource Cleanup](#resource-cleanup)
9. [Requirements Summary](#requirements-summary)
10. [Document Change History](#document-change-history)
11. [References](#references)

---

# Overview

This document specifies the requirements for the **AWS Object Storage** Universal Extension for Stonebranch Universal Automation Center (UAC).

**Integration Purpose:** The extension provides a simple AWS S3 integration that allows UAC tasks to list objects in an S3 bucket and upload local files from the Universal Agent host to a specified S3 bucket. The purpose is to demonstrate that AWS S3 integration can be implemented with Stonebranch; it is scoped as an MVP/demo integration.

---

# Actions

## Action 1: List Objects

**Functional Requirements:**

1. The extension must list all objects in a specified AWS S3 bucket using the AWS `list_objects_v2` API.
2. For each object, the following attributes must be retrieved and displayed: object Key (full path/name), Size in bytes, and Last Modified timestamp (UTC).
3. The STDOUT output must be formatted as an ASCII table with three columns — Key, Size (bytes), and Last Modified — using the `tabulate` library with `tablefmt="rounded_outline"`.
4. The Extension Output (JSON) must include a total `object_count` and an array of objects, each containing `key`, `size_bytes`, and `last_modified` fields.
5. The total number of objects returned must be capped at the value defined by the `UE_MAX_OUTPUT_RECORDS` environment variable (default: 100).
6. When the output is truncated because the object count in the bucket exceeds `UE_MAX_OUTPUT_RECORDS`, a truncation notice must be written to STDOUT, STDERR, and included in the Extension Output metadata, indicating how many total objects exist versus how many were returned.
7. The output-only `Status` field must be populated with: `"Listed N objects"` (where N is the number of objects returned).
8. The output-only `Result` field must be populated with: `"N objects in <bucket-name>"`.

---

## Action 2: Upload File

**Functional Requirements:**

1. The extension must upload a local file from the Universal Agent host filesystem to a specified AWS S3 bucket and S3 object key using the `boto3` SDK.
2. The STDOUT output must confirm a successful upload in the format: `"Uploaded <local_file> to s3://<bucket>/<s3_key>"`.
3. The Extension Output (JSON) must include: `s3_uri`, `bucket`, `key`, and `etag` (the MD5 hash returned by the S3 API upon successful upload).
4. The output-only `Status` field must be populated with: `"Upload successful"`.
5. The output-only `Result` field must be populated with the full S3 URI: `"s3://<bucket>/<s3_key>"`.
6. Before attempting the upload, the extension must validate that the specified local file exists on the agent host. If the file does not exist, a validation error must be raised with return code `20`.

---

# Input Requirements

## Connection Parameters

These fields are required for all actions.

- **AWS Credentials** (Credential, mandatory):
  A UAC Credential entity holding the AWS authentication values.
  - The `user` attribute must contain the **AWS Access Key ID**.
  - The `password` attribute must contain the **AWS Secret Access Key**.
  - Applicability: All actions (List Objects, Upload File).

- **AWS Region** (Text, mandatory):
  The AWS region where the target S3 bucket resides.
  - Example: `us-east-1`
  - Applicability: All actions.

- **Bucket Name** (Text, mandatory):
  The name of the AWS S3 bucket to operate on.
  - Example: `my-demo-bucket`
  - Applicability: All actions.

## Action-Specific Parameters

- **Action** (Choice, mandatory):
  Determines which operation the extension executes.
  - Available options:
    - `List Objects` — lists objects in the specified bucket.
    - `Upload File` — uploads a local file to the specified bucket.
  - Default presented option: `List Objects`.
  - Showing/hiding logic:
    - When `List Objects` is selected: Local File and S3 Object Key fields are hidden.
    - When `Upload File` is selected: Local File and S3 Object Key fields are shown and required.

- **Local File** (Text, conditional — required when Action is `Upload File`):
  The absolute path to the local file on the Universal Agent host to be uploaded.
  - Example: `/data/reports/file.csv`
  - Applicability: Upload File action only.

- **S3 Object Key** (Text, conditional — required when Action is `Upload File`):
  The target S3 object key (path and filename) within the bucket.
  - Example: `data/reports/file.csv`
  - Applicability: Upload File action only.

---

# Output Requirements

## On Success

**Return code:** `0`

### List Objects Action

- **Status description:** `"Listed N objects"` (N = number of objects returned)
- **Output-only fields:**
  - `Status` (Text): `"Listed N objects"`
  - `Result` (Text): `"N objects in <bucket-name>"`
- **Extension output (JSON):**
  ```json
  {
    "result": {
      "object_count": 42,
      "objects": [
        {
          "key": "data/file1.csv",
          "size_bytes": 1024,
          "last_modified": "2026-09-15T10:30:00+00:00"
        }
      ]
    }
  }
  ```
  When truncated, the JSON must also include a `truncated` boolean and a `total_count` integer indicating the actual number of objects in the bucket.
- **STDOUT output:** ASCII table formatted with `tabulate` (`tablefmt="rounded_outline"`) containing columns: Key, Size (bytes), Last Modified. When truncated, a notice must follow the table indicating truncation and the total object count.
- **Success Criteria:**
  1. The S3 API call completes without error.
  2. Object metadata is retrieved and formatted correctly.
  3. STDOUT contains the ASCII table.
  4. Extension Output JSON is populated with `object_count` and `objects` array.
  5. Output-only `Status` and `Result` fields are populated.

### Upload File Action

- **Status description:** `"Upload successful"`
- **Output-only fields:**
  - `Status` (Text): `"Upload successful"`
  - `Result` (Text): `"s3://<bucket>/<s3_key>"`
- **Extension output (JSON):**
  ```json
  {
    "result": {
      "s3_uri": "s3://my-demo-bucket/data/reports/file.csv",
      "bucket": "my-demo-bucket",
      "key": "data/reports/file.csv",
      "etag": "d41d8cd98f00b204e9800998ecf8427e"
    }
  }
  ```
- **STDOUT output:** `"Uploaded /data/reports/file.csv to s3://my-demo-bucket/data/reports/file.csv"`
- **Success Criteria:**
  1. The local file exists and is readable on the agent host.
  2. The S3 upload API call completes without error.
  3. STDOUT contains the confirmation message with the S3 URI.
  4. Extension Output JSON is populated with `s3_uri`, `bucket`, `key`, and `etag`.
  5. Output-only `Status` and `Result` fields are populated.

---

## On Error

### Failure Scenarios

**Validation Error (return code: `20`)**

| Scenario | Description | Root Causes | Status Description Pattern |
|---|---|---|---|
| Local file not found | The specified local file path does not exist on the agent host | Incorrect path, file not yet created, wrong agent | `"Validation Error: Local file <path> not found"` |
| Missing required field | A mandatory input field has no value | User did not provide a required field | `"Validation Error: <field_name> is required"` |

**Runtime Failure (return code: `1`)**

| Scenario | Description | Root Causes | Status Description Pattern |
|---|---|---|---|
| Authentication failure | AWS credentials are invalid or expired | Incorrect Access Key ID or Secret Access Key | `"S3 Error: Authentication failed"` |
| Bucket not found | The specified S3 bucket does not exist or is inaccessible | Typo in bucket name, wrong region, no access | `"S3 Error: Bucket <name> not found or inaccessible"` |
| Permission denied | IAM policy does not allow the requested S3 operation | Insufficient IAM permissions | `"S3 Error: Access Denied for bucket <name>"` |
| Connection timeout | Network connectivity issue to AWS | Network outage, DNS failure | `"S3 Error: Connection timeout reaching AWS"` |
| Upload interrupted | File upload fails partway through | Network drop, agent host disk issue | `"S3 Error: Upload failed for <local_file>"` |

- **STDERR:** Error details must be written to STDERR for all failure scenarios.
- **Input Validation:** Input validation must occur before any AWS API call is made. Validation failures must return code `20`.

---

# Authentication Requirements

The extension supports **static AWS IAM credentials only**. Authentication is performed by passing the AWS Access Key ID and AWS Secret Access Key directly to the `boto3` S3 client at runtime. Temporary credentials (AWS STS session tokens) are not supported.

Credentials must be supplied via a UAC Credential field entity:
- `user` attribute → AWS Access Key ID
- `password` attribute → AWS Secret Access Key

---

# Environment Variables

- **`UE_MAX_OUTPUT_RECORDS`**: Controls the maximum number of S3 objects returned and displayed by the List Objects action. Default value: `100`. Users who need to retrieve more objects may set this variable at the UAC task or agent level. Does not affect the Upload File action.

---

# Operational Behavior

**Dynamic Choice Fields:**
Not applicable. No dynamic dropdowns are required.

**Cancel Action:**
Standard UAC task cancellation behavior applies. No special cleanup is required.

**Re-run Capability:**
Both actions support re-run. Re-running a List Objects task re-queries the bucket. Re-running an Upload File task re-uploads the file, overwriting any existing S3 object at the same key.

**Progress Reporting:**
No progress bar is required. Basic informational log messages may be written to STDOUT during execution (e.g., connecting to S3, starting upload). A final confirmation or error message must always be written to STDOUT.

**Dynamic Commands:**
Not applicable.

---

# Implementation Notes

## Python Compatibility

Targeting compatibility for Python >= 3.11 (as specified in the extension metadata).

## Target Platform

Linux only (OS: Linux, Architecture: x86_64). C extension modules with a confirmed `manylinux_2_17_x86_64` wheel are viable in addition to pure-Python modules.

## Third-Party Services and Tools

**AWS S3 (Simple Storage Service)**
- Service: Amazon Web Services S3 object storage
- Version constraints: No specific API version constraint; latest `list_objects_v2` and `put_object` / `upload_file` APIs.
- Integration approach: The `boto3` Python SDK is used exclusively for all S3 interactions. No direct HTTP calls to AWS APIs.

**boto3**
- Short description: Official AWS SDK for Python; provides all S3 operations.
- Version: `1.43.108` (pinned)
- Type: Pure-Python
- boto3's transitive dependencies (`botocore`, `s3transfer`, `jmespath`, `urllib3`, `python-dateutil`) must be bundled automatically.

**tabulate**
- Short description: ASCII table formatter for STDOUT display of object listings.
- Version: `0.10.0` (pinned)
- Type: Pure-Python

## Error Handling

- **Error categories:**
  - Validation errors: missing required fields, local file not found (caught before AWS API calls).
  - Authentication errors: invalid or expired AWS credentials.
  - S3 access errors: bucket not found, permission denied.
  - Network errors: connection timeout, connectivity failure.
  - Upload errors: interrupted transfer.
- **Error handling strategy:** All errors must be caught and produce a human-readable message on STDERR and in the Status Description. The appropriate return code (`1` for runtime failures, `20` for validation errors) must be set.
- **Recovery mechanisms:** No automatic retry logic is required for the MVP.

## Resource Cleanup

- **Cleanup scenarios:** No persistent resources (open file handles, network sockets held open) require explicit cleanup beyond what the `boto3` client handles internally.
- **Strategy:** Standard Python context management and `boto3` client lifecycle apply; no special teardown logic is required.

---

# Requirements Summary

| # | Requirement | Action(s) |
|---|---|---|
| R1 | List objects in a specified AWS S3 bucket using `list_objects_v2` | List Objects |
| R2 | Display Key, Size (bytes), and Last Modified for each object in an ASCII table on STDOUT | List Objects |
| R3 | Return a JSON Extension Output with `object_count` and per-object `key`, `size_bytes`, `last_modified` | List Objects |
| R4 | Cap output at `UE_MAX_OUTPUT_RECORDS` (default 100); include truncation notice when limit is reached | List Objects |
| R5 | Populate output-only `Status` with `"Listed N objects"` and `Result` with `"N objects in <bucket>"` | List Objects |
| R6 | Upload a local file from the agent host to a specified S3 bucket and object key | Upload File |
| R7 | Validate that the local file exists before attempting upload | Upload File |
| R8 | Write confirmation to STDOUT: `"Uploaded <local_file> to s3://<bucket>/<key>"` | Upload File |
| R9 | Return JSON Extension Output with `s3_uri`, `bucket`, `key`, and `etag` | Upload File |
| R10 | Populate output-only `Status` with `"Upload successful"` and `Result` with S3 URI | Upload File |
| R11 | Use static AWS credentials (Access Key ID via `user`, Secret Access Key via `password`) | All |
| R12 | Accept AWS Region and Bucket Name as mandatory input fields | All |
| R13 | Use return code `0` for success, `1` for runtime failures, `20` for validation errors | All |
| R14 | Bundle `boto3==1.43.108` and `tabulate==0.10.0` with the extension | All |

---

# Document Change History

- **2026-10-06**: Initial requirements — Moderate Detail level.
- **2026-10-06 03:30:00**: Comprehensive refinement based on 7 clarification questions and user feedback covering credential mapping, output content and format, record limit strategy, upload confirmation, output-only field design, and return code convention.

---

# References

- Original Requirements Document: `memory/requirements.md`
- Original Requirements Q&A Document: `memory/agents-memory/requirements-QnA.md`

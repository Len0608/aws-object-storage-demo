# Universal Extension Requirements (Refined)

**Extension Name:** AWS Object Storage
**Original Generated:** 2026-10-08
**Refined:** 2026-10-08
**Agent_id:** N/A
**Requirements Completeness:** Moderate Detail
**Target Platform:** Linux

---

# Table of Contents

1. [Overview](#overview)
2. [Actions](#actions)
   - 2.1 [Action 1 — List Objects](#action-1--list-objects)
   - 2.2 [Action 2 — Upload File](#action-2--upload-file)
3. [Input Requirements](#input-requirements)
   - 3.1 [Connection Parameters](#31-connection-parameters)
   - 3.2 [Bucket Parameters](#32-bucket-parameters)
   - 3.3 [Upload-Specific Parameters](#33-upload-specific-parameters)
4. [Output Requirements](#output-requirements)
   - 4.1 [On Success](#41-on-success)
   - 4.2 [On Error](#42-on-error)
5. [Authentication Requirements](#authentication-requirements)
6. [Environment Variables](#environment-variables)
7. [Operational Behavior](#operational-behavior)
8. [Implementation Notes](#implementation-notes)
   - 8.1 [Python Compatibility](#81-python-compatibility)
   - 8.2 [Target Platform](#82-target-platform)
   - 8.3 [Third-Party Services and Tools](#83-third-party-services-and-tools)
   - 8.4 [Error Handling](#84-error-handling)
   - 8.5 [Resource Cleanup](#85-resource-cleanup)
9. [Requirements Summary](#requirements-summary)
10. [Document Change History](#document-change-history)
11. [References](#references)

---

# Overview

This document defines the requirements for the **AWS Object Storage** Universal Extension for Stonebranch Universal Automation Center (UAC).

**Integration Purpose:** The extension provides a simple AWS S3 integration that allows UAC tasks to list objects in an S3 bucket and upload local files from the Universal Agent host to an S3 bucket. It is an MVP/demo integration intended to demonstrate that AWS S3 operations can be implemented via Stonebranch, and must be kept as simple as possible.

---

# Actions

## Action 1 — List Objects

**Functional Requirements:**

1. The extension must connect to AWS S3 using the provided credentials and region.
2. The extension must list objects in the specified S3 bucket.
3. The listing must display the following columns per object: Key, Size (in bytes), Last Modified.
4. STDOUT must present the object listing as an ASCII table using `rounded_outline` format.
5. The number of objects displayed must be capped at a configurable maximum (default: 100). Objects beyond the cap are counted but not listed inline.
6. When the output is truncated, STDOUT must include a note: `Note: Displaying <cap> of <total> objects. Set UE_MAX_OUTPUT_RECORDS to increase.`
7. The total object count must be reported in the `Result Summary` output-only field as: `"<N> objects found in bucket"`.
8. The Extension Output must contain a JSON structure with the total object count and the displayed object records (up to the cap).

---

## Action 2 — Upload File

**Functional Requirements:**

1. The extension must connect to AWS S3 using the provided credentials and region.
2. The extension must upload the specified local file from the Universal Agent host to the specified S3 bucket and S3 object key.
3. On successful upload, STDOUT must print a success confirmation: `Uploaded: s3://<bucket>/<key>`.
4. The `Result Summary` output-only field must be set to: `"Uploaded: s3://<bucket>/<key>"`.
5. The Extension Output must contain a JSON structure with the bucket name, S3 object key, and the size of the uploaded file (in bytes).
6. The status description must be: `Success: File uploaded to s3://<bucket>/<key>`.

---

# Input Requirements

## 3.1 Connection Parameters

- **Action** (choice, required): Selects the operation to perform.
  - Options: `List Objects`, `Upload File`
  - Default: `List Objects`
  - Applicability: All actions

- **AWS Credentials** (credential, required): UAC Credential field used for AWS authentication.
  - `user` attribute → AWS Access Key ID
  - `password` attribute → AWS Secret Access Key
  - Applicability: All actions

- **AWS Region** (text, required): The AWS region identifier where the target S3 bucket resides.
  - Example: `us-east-1`
  - Default Value: `us-east-1`
  - Applicability: All actions

## 3.2 Bucket Parameters

- **Bucket Name** (text, required): The name of the S3 bucket to operate on.
  - Example: `my-demo-bucket`
  - Applicability: All actions

## 3.3 Upload-Specific Parameters

- **Local File** (text, required for Upload File): The absolute path to the local file on the Universal Agent host to be uploaded.
  - Example: `/tmp/reports/jan-2026.csv`
  - Applicability: Upload File only

- **S3 Object Key** (text, required for Upload File): The destination object key (path and filename) within the S3 bucket.
  - Example: `reports/jan-2026.csv`
  - Applicability: Upload File only

---

# Output Requirements

## 4.1 On Success

**Return code:** 0

**Output-only field (shared across actions):**
- **Result Summary** (text): A short summary string populated at runtime.
  - List Objects: `"<N> objects found in bucket"`
  - Upload File: `"Uploaded: s3://<bucket>/<key>"`

### List Objects — Success

**Status description:** `Success: Listed <N> objects in <bucket>`

**STDOUT output:**
- ASCII table in `rounded_outline` format with columns: Key, Size (B), Last Modified.
- If truncated: followed by `Note: Displaying <cap> of <total> objects. Set UE_MAX_OUTPUT_RECORDS to increase.`

**Extension Output (JSON):**
```json
{
  "bucket": "my-demo-bucket",
  "object_count": 42,
  "displayed_count": 42,
  "objects": [
    {
      "key": "reports/jan-2026.csv",
      "size": 184320,
      "last_modified": "2026-01-15T09:23:41Z"
    }
  ]
}
```

**Success Criteria:**
1. S3 API call completes without error.
2. STDOUT contains the ASCII table.
3. `Result Summary` output field is populated.
4. Extension Output JSON is valid and contains the object list.

### Upload File — Success

**Status description:** `Success: File uploaded to s3://<bucket>/<key>`

**STDOUT output:** `Uploaded: s3://<bucket>/<key>`

**Extension Output (JSON):**
```json
{
  "bucket": "my-demo-bucket",
  "key": "reports/jan-2026.csv",
  "file_size": 184320
}
```

**Success Criteria:**
1. S3 upload call completes without error.
2. STDOUT contains the confirmation message.
3. `Result Summary` output field is populated.
4. Extension Output JSON is valid and contains bucket, key, and file size.

## 4.2 On Error

**Failure Scenarios:**

- **Authentication Failure**
  - Description: AWS rejects the provided credentials.
  - Root causes: Invalid Access Key ID, invalid Secret Access Key, or expired credentials.
  - Return code: 1
  - Status description pattern: `Error: Authentication failed — <AWS error message>`

- **Bucket Not Found**
  - Description: The specified S3 bucket does not exist or is not accessible.
  - Root causes: Incorrect bucket name, wrong region, insufficient IAM permissions.
  - Return code: 1
  - Status description pattern: `Error: Bucket '<bucket>' not found or not accessible — <AWS error message>`

- **Local File Not Found** (Upload File only)
  - Description: The specified local file path does not exist on the agent host.
  - Root causes: Incorrect path, file deleted before task execution.
  - Return code: 1
  - Status description pattern: `Error: Local file not found — <path>`

- **Upload Failure** (Upload File only)
  - Description: The upload call fails mid-transfer.
  - Root causes: Network interruption, S3 write permission denied, disk read error.
  - Return code: 1
  - Status description pattern: `Error: Upload failed — <AWS error message>`

- **Invalid Region**
  - Description: The provided region identifier is not recognized by AWS.
  - Root causes: Typo or invalid region string.
  - Return code: 1
  - Status description pattern: `Error: Invalid region '<region>' — <AWS error message>`

**Input Validation:**
- Input fields validation is required. Missing required fields must produce a descriptive error before any API call is made.

---

# Authentication Requirements

The extension uses AWS Access Key ID / Secret Access Key authentication via a single UAC Credential field. The `user` attribute of the credential holds the AWS Access Key ID; the `password` attribute holds the AWS Secret Access Key. These values are passed directly to the boto3 S3 client for request signing. No IAM Instance Role or other authentication mechanism is required.

---

# Environment Variables

- **`UE_MAX_OUTPUT_RECORDS`**: Integer. Controls the maximum number of S3 objects displayed in STDOUT and included in Extension Output for the List Objects action. Default: `100`. Objects beyond the limit are counted but not listed. A warning note is appended to STDOUT when truncation occurs.

---

# Operational Behavior

**Dynamic Choice Fields:**
Not applicable. No dynamic choice population is required.

**Cancel Action:**
Standard UAC task cancellation behavior applies. No special cancel handling is required beyond what the UAC framework provides.

**Re-run Capability:**
Tasks may be re-run using standard UAC re-run behavior. No special state management is required between runs.

**Progress Reporting:**
No progress bar is required. The extension must log key steps to STDOUT (e.g., connecting to S3, listing objects, uploading file) so that the UAC task log reflects progress.

**Dynamic Commands:**
Not applicable. No dynamic commands are required.

---

# Implementation Notes

## 8.1 Python Compatibility

Not specified specifically. Targeting compatibility for Python 3.11.

## 8.2 Target Platform

Linux (x86_64). C extension modules with a confirmed `manylinux_2_17_x86_64` wheel are viable in addition to pure-Python modules. All required dependencies for this extension are pure-Python, so no wheel compatibility issues are anticipated.

## 8.3 Third-Party Services and Tools

**boto3**
- Short Description: AWS SDK for Python. Provides the S3 client used for listing objects and uploading files.
- Version: 1.43.109
- Type: Pure Python
- Integration approach: Used to construct an S3 client authenticated with AWS Access Key ID and Secret Access Key, then invoke `list_objects_v2` or `upload_file` accordingly.

**botocore**
- Short Description: Core AWS protocol, request signing, and retry logic. Required transitive dependency of boto3.
- Version: 1.43.109
- Type: Pure Python

**s3transfer**
- Short Description: Manages multipart S3 transfers. Required transitive dependency of boto3, used internally by `upload_file()`.
- Version: 0.19.2
- Type: Pure Python

**jmespath**
- Short Description: JSON query language library. Required transitive dependency of boto3/botocore for response parsing.
- Version: 1.1.0
- Type: Pure Python

**tabulate**
- Short Description: Formats tabular data as ASCII tables. Used to render the object listing on STDOUT in `rounded_outline` format.
- Version: 0.10.0
- Type: Pure Python

All dependencies must be bundled with the Universal Extension. Nothing may require separate installation on the Universal Agent.

## 8.4 Error Handling

**High-level error categories:**
- Authentication errors (invalid or expired credentials)
- Resource not found errors (bucket or local file)
- Permission / authorization errors (IAM policy denial)
- Network / connectivity errors
- Input validation errors (missing or invalid field values)

**Error handling strategy:** All AWS API exceptions must be caught and translated into a descriptive status message and a non-zero return code. The error message must include enough detail (AWS error code or message) to allow the operator to diagnose the issue.

**Recovery mechanisms:** None. The extension is stateless per execution. No automatic retry logic is required for the MVP.

## 8.5 Resource Cleanup

**Cleanup scenarios:** The boto3 S3 client and any open file handles used during upload must be released after the operation completes, whether it succeeds or fails.

**Strategy:** Standard Python context management (`with` statements or explicit close calls) must be used to ensure file handles are closed and client connections are released on both success and error paths.

---

# Requirements Summary

The **AWS Object Storage** extension is a minimal, demo-grade Universal Extension for UAC providing two S3 operations:

1. **List Objects** — lists objects in an S3 bucket and displays Key, Size, and Last Modified in a formatted ASCII table, capped at 100 records by default (overridable via `UE_MAX_OUTPUT_RECORDS`).
2. **Upload File** — uploads a local file from the agent host to a specified S3 bucket and key, reporting the S3 path and file size on success.

Authentication uses a UAC Credential field with `user` = AWS Access Key ID and `password` = AWS Secret Access Key. A single `Result Summary` output-only field surfaces the key result in the UAC task instance panel for both actions. The AWS Region field defaults to `us-east-1`. All dependencies (boto3, botocore, s3transfer, jmespath, tabulate) are pure-Python and must be bundled with the extension. The extension targets Linux x86_64 and Python 3.11.

---

# Document Change History

- **2026-10-08**: Initial requirements — Moderate Detail. Two actions (List Objects, Upload File), boto3 SDK, MVP/demo scope.
- **2026-10-08**: Comprehensive refinement based on 6 clarification questions and user feedback. Added: credential attribute mapping, STDOUT column selection, output record cap with environment variable override, upload success reporting, output-only field design, and AWS Region default value.

---

# References

- Original Requirements Document: `memory/requirements.md`
- Original Requirements Q&A Document: `memory/agents-memory/requirements-QnA.md`

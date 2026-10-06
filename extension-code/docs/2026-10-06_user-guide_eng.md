> **Version:** 1.0.0 | **Date:** 2026-10-06

# AWS Object Storage Demo — User Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Task Actions](#task-actions)
4. [Task Configuration](#task-configuration)
5. [Example Walkthrough](#example-walkthrough)
6. [Troubleshooting](#troubleshooting)
7. [Field Reference](#field-reference)

---

## Overview

The **AWS Object Storage Demo** Universal Extension integrates Stonebranch UAC with Amazon S3. It provides two operations:

- **List Objects** — retrieves and displays all objects in a specified S3 bucket, printing a summary table (key, size, last modified) to the task output.
- **Upload File** — uploads a file from the UAC agent host to a target S3 bucket and key, then reports the resulting S3 URI.

This extension is intended for use in automation workflows that need to audit bucket contents or deliver files to S3 as part of a larger pipeline.

---

## Prerequisites

- A Stonebranch UAC environment running release **7.6.0.0 or later**.
- The `aws-object-storage-demo` extension (v1.0.0) installed and registered in UAC.
- A UAC Agent running Python **3.11 or later** with network access to the AWS S3 endpoint for the target region.
- An AWS IAM user or role with the following permissions at minimum:
  - `s3:ListBucket` — required for **List Objects**.
  - `s3:PutObject` — required for **Upload File**.
- A UAC **Credential** entity configured with:
  - **Username** field = AWS Access Key ID
  - **Password** field = AWS Secret Access Key

---

## Task Actions

### List Objects

Paginates through all objects in the target S3 bucket and prints an ASCII table to STDOUT containing each object's key, size, and last-modified timestamp. Output is capped at 100 records by default (`UE_MAX_OUTPUT_RECORDS`).

**When to use:** Auditing bucket contents, verifying a file was delivered by a prior step, or reporting inventory.

**Execution flow:**

1. UAC sends the task to the agent; the extension reads all input fields.
2. Input validation runs: credentials, region, and bucket name are checked for completeness.
3. The extension connects to S3 in the specified region using the provided credentials.
4. All objects are paginated and collected (up to the output cap).
5. An ASCII table is written to STDOUT.
6. The `status` output field is set to a short summary (e.g., `Listed 42 objects`).
7. The `result` output field is set to the object count string.
8. The task completes with exit code 0.

**Completion behavior:** The task status in UAC reflects success/failure. The `status` and `result` output fields are preserved on re-run (`preserveOutputOnRerun = true`).

---

### Upload File

Validates that the specified local file exists on the agent host, then uploads it to the target S3 bucket at the given key. After a successful upload, it retrieves the ETag and confirms the operation.

**When to use:** Delivering pipeline outputs, reports, or data files to S3 as part of an automated workflow.

**Execution flow:**

1. UAC sends the task to the agent; the extension reads all input fields.
2. Input validation runs: credentials, region, bucket name, local file path, and S3 object key are all checked.
3. The extension verifies the local file exists on the agent host (`os.path.isfile()`). If not, the task fails immediately with a clear error message before any AWS call is made.
4. The extension connects to S3 and uploads the file using the boto3 client.
5. The ETag of the uploaded object is retrieved and logged.
6. A confirmation line is written to STDOUT, including the full S3 URI.
7. The `status` output field is set to a summary (e.g., `Uploaded successfully`).
8. The `result` output field is set to the full S3 URI (e.g., `s3://my-bucket/data/reports/file.csv`).
9. The task completes with exit code 0.

**Completion behavior:** Same as List Objects. Output fields are preserved across re-runs.

---

## Task Configuration

### Authentication

| Field | Description | Required | Example |
|-------|-------------|----------|---------|
| AWS Credentials | UAC Credential entity whose **Username** is the AWS Access Key ID and **Password** is the AWS Secret Access Key. Supports UAC variable substitution. | Yes | `my-aws-cred` |

### Operation

| Field | Description | Required | Accepted Values | Default |
|-------|-------------|----------|-----------------|---------|
| Action | The S3 operation to perform. Controls which fields are shown on the task form. | No | `List Objects`, `Upload File` | `List Objects` |

### Target

| Field | Description | Required | Example |
|-------|-------------|----------|---------|
| AWS Region | AWS region where the S3 bucket resides. | Yes | `us-east-1` |
| Bucket Name | Name of the S3 bucket to operate on. | Yes | `my-demo-bucket` |

### Upload Only (visible when Action = "Upload File")

| Field | Description | Required | Example |
|-------|-------------|----------|---------|
| Local File Path | Absolute path to the file on the agent host. Required when the action is Upload File. | Yes (if Upload File) | `/data/reports/report.csv` |
| S3 Object Key | Target key (path) within the bucket where the file will be stored. Required when the action is Upload File. | Yes (if Upload File) | `data/reports/report.csv` |

### Output (read-only, populated by the extension)

| Field | Description |
|-------|-------------|
| Status | Short summary of the operation outcome. Shown in the UAC task list view. |
| Result | Key result: total object count (List Objects) or full S3 URI (Upload File). Shown in the UAC task list view. |

---

## Example Walkthrough

### Scenario 1 — List All Objects in a Bucket

**Goal:** Retrieve a full listing of objects in an S3 bucket to verify bucket contents.

**Prerequisites:**
- A UAC Credential named `aws-prod-cred` exists with a valid Access Key ID and Secret Access Key.
- The IAM user has `s3:ListBucket` permission on the target bucket.
- The UAC Agent has outbound HTTPS access to `s3.us-east-1.amazonaws.com`.

**Configuration:**

| Field | Value | Notes |
|-------|-------|-------|
| Action | `List Objects` | Default; no upload fields appear. |
| AWS Credentials | `aws-prod-cred` | Select the credential from the dropdown. |
| AWS Region | `us-east-1` | Must match the bucket's region. |
| Bucket Name | `acme-data-lake` | Case-sensitive. |
| Local File Path | *(hidden)* | Not applicable for List Objects. |
| S3 Object Key | *(hidden)* | Not applicable for List Objects. |

**What happens:**
- The extension connects to S3 in `us-east-1` and paginates all objects in `acme-data-lake`.
- An ASCII table of object keys, sizes, and last-modified dates is written to the task output log.
- Output is capped at 100 records.
- The `status` field shows `Listed N objects`; the `result` field shows the count.
- The task completes with exit code 0 and a Success status in UAC.

---

### Scenario 2 — Upload a Report File to S3

**Goal:** Deliver a generated report from the agent host to a specific location in S3.

**Prerequisites:**
- A UAC Credential named `aws-etl-cred` exists with a valid Access Key ID and Secret Access Key.
- The IAM user has `s3:PutObject` permission on the target bucket and key prefix.
- The file `/opt/reports/daily_summary.csv` exists on the UAC Agent host at task execution time.
- The UAC Agent has outbound HTTPS access to the S3 endpoint for `eu-west-1`.

**Configuration:**

| Field | Value | Notes |
|-------|-------|-------|
| Action | `Upload File` | Reveals Local File Path and S3 Object Key fields. |
| AWS Credentials | `aws-etl-cred` | Select the credential from the dropdown. |
| AWS Region | `eu-west-1` | Must match the bucket's region. |
| Bucket Name | `acme-reports` | Bucket must already exist. |
| Local File Path | `/opt/reports/daily_summary.csv` | Absolute path on the agent host. |
| S3 Object Key | `reports/2026/10/daily_summary.csv` | Target path within the bucket; no leading slash. |

**What happens:**
- The extension validates the local file exists on the agent host before making any AWS API call.
- The file is uploaded to `s3://acme-reports/reports/2026/10/daily_summary.csv`.
- A confirmation line including the ETag and S3 URI is written to the task output log.
- The `status` field shows `Uploaded successfully`; the `result` field shows the full S3 URI.
- The task completes with exit code 0 and a Success status in UAC.

---

## Troubleshooting

### Authentication Failures

**Symptom:** Task fails with an error referencing `InvalidClientTokenId`, `AuthFailure`, `SignatureDoesNotMatch`, or `InvalidAccessKeyId`.

**Possible cause:** The UAC Credential entity contains an incorrect or expired AWS Access Key ID or Secret Access Key.

**Resolution:**
1. Open the UAC Credential used in the task.
2. Verify the **Username** field holds the Access Key ID and the **Password** field holds the Secret Access Key.
3. Confirm the key is active in the AWS IAM console.
4. Re-run the task after correcting the credential.

---

### Permission Errors

**Symptom:** Task fails with `AccessDenied`.

**Possible cause:** The IAM user or role associated with the credentials lacks the required permission (`s3:ListBucket` or `s3:PutObject`) on the target bucket.

**Resolution:**
1. Identify the IAM identity used (Access Key ID maps to an IAM user or assumed role).
2. In the AWS IAM console, attach or update the policy to grant the required S3 permissions.
3. Confirm the policy applies to the correct bucket ARN (e.g., `arn:aws:s3:::my-bucket` and `arn:aws:s3:::my-bucket/*`).
4. Re-run the task.

---

### Bucket Not Found

**Symptom:** Task fails with `NoSuchBucket`.

**Possible cause:** The bucket name or region is incorrect, or the bucket does not exist.

**Resolution:**
1. Verify the **Bucket Name** field matches the exact bucket name in AWS (case-sensitive).
2. Verify the **AWS Region** field matches the region where the bucket was created.
3. Confirm the bucket exists in the AWS S3 console.
4. Re-run the task after correcting the values.

---

### Local File Not Found (Upload File only)

**Symptom:** Task fails before any AWS API call with a validation error indicating the file path does not exist.

**Possible cause:** The path in **Local File Path** is incorrect, the file has not yet been generated, or it is on a different host than the selected UAC Agent.

**Resolution:**
1. Confirm the file exists at the specified absolute path on the agent host.
2. Ensure the task is assigned to the correct UAC Agent (the one where the file resides).
3. If the file is generated by a prior workflow step, add a dependency to ensure the upstream task completes before this task runs.

---

### Network / Connectivity Issues

**Symptom:** Task fails with a connection timeout or endpoint connection error.

**Possible cause:** The UAC Agent cannot reach the AWS S3 endpoint for the specified region over HTTPS (port 443).

**Resolution:**
1. Verify the agent host has outbound internet or VPC access to `s3.<region>.amazonaws.com`.
2. Check firewall rules and security group policies.
3. If connectivity is intermittent, re-running the task may succeed; otherwise, resolve the network path before retrying.

---

### Field Dependency Violations

**Symptom:** Task fails at input validation with a message about a missing required field.

**Possible cause:** The **Action** is set to `Upload File` but **Local File Path** or **S3 Object Key** is empty.

**Resolution:**
1. Set the **Action** field to `Upload File`.
2. Provide a value for both **Local File Path** and **S3 Object Key**.
3. Both fields are required when the Upload File action is selected and will be validated before any other processing.

---

### Unexpected System Error

**Symptom:** Task fails with an `UnexpectedSystemError` and an exception type name in the message.

**Possible cause:** An unhandled runtime error occurred in the extension (e.g., a Python exception not covered by specific error types).

**Resolution:**
1. Review the full task output log in UAC for the exception type and message.
2. Check that the extension version matches your UAC environment requirements (Python ≥ 3.11, UAC ≥ 7.6.0.0).
3. Contact your Stonebranch administrator or support with the full task output log if the cause is unclear.

---

## Field Reference

| # | Field Name | Label | Type | Required | Default | Description | Allowed Values |
|---|-----------|-------|------|----------|---------|-------------|----------------|
| 0 | `action` | Action | Choice | No | `List Objects` | Selects the S3 operation to perform. Controls conditional visibility of upload-specific fields. | `List Objects`, `Upload File` |
| 1 | `aws_credentials` | AWS Credentials | Credential | Yes | — | UAC Credential entity. Username = AWS Access Key ID; Password = AWS Secret Access Key. Supports variable substitution. | Any valid UAC Credential name |
| 2 | `aws_region` | AWS Region | Text | Yes | — | AWS region identifier where the target bucket resides. | e.g., `us-east-1`, `eu-west-1`, `ap-southeast-2` |
| 3 | `bucket_name` | Bucket Name | Text | Yes | — | Name of the S3 bucket to operate on. Case-sensitive. | Any valid S3 bucket name |
| 4 | `local_file` | Local File Path | Text | Yes (Upload File only) | — | Absolute path to the file on the agent host to upload. Visible and required only when Action = Upload File. | Absolute filesystem path, e.g., `/data/file.csv` |
| 5 | `s3_object_key` | S3 Object Key | Text | Yes (Upload File only) | — | Target object key within the bucket. Visible and required only when Action = Upload File. No leading slash. | e.g., `reports/2026/file.csv` |
| 6 | `status` | Status | Text (Output Only) | No | — | Short outcome summary populated by the extension after execution. Shown in the UAC task list view. | Populated by extension; read-only |
| 7 | `result` | Result | Text (Output Only) | No | — | Key result: object count string (List Objects) or full S3 URI (Upload File). Shown in the UAC task list view. | Populated by extension; read-only |

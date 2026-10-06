# AWS Object Storage Demo - Implementation Analysis

**Extension Name:** *AWS Object Storage Demo (aws-object-storage-demo)*
**Universal Template Name:** *Aws Object Storage Demo*
**Target Platform:** Linux

---

## Extension Overview

The AWS Object Storage Demo extension provides a two-action S3 integration for Stonebranch UAC. It enables UAC tasks to list objects in an S3 bucket (with capped output and truncation notices) and upload local files from the Universal Agent host to a specified S3 bucket and key. All S3 interactions use the `boto3` SDK exclusively with static IAM credentials. This is an MVP/demo-scoped integration.

---

# Template Fields

## 1. Input Fields

**action**
- **Type**: Choice Field (Single-select)
- **Visible When**: always
- **Required When**: always
- **Options**:
  - *List Objects* — Lists all objects in the specified S3 bucket and displays them as an ASCII table
  - *Upload File* — Uploads a local file from the agent host to the specified S3 bucket and key
- **Default Value**: List Objects
- **Validation**:
  - Must be one of the options
- **Purpose**: Selects which S3 operation the extension performs

**aws_credentials**
- **Type**: Credential Field
- **Visible When**: always
- **Required When**: always
- **Validation**:
  - Must reference a valid UAC Credential entity
  - `user` attribute must contain the AWS Access Key ID
  - `password` attribute must contain the AWS Secret Access Key
- **Purpose**: Provides static AWS IAM credentials for authenticating with the S3 service. The `user` attribute holds the Access Key ID and `password` holds the Secret Access Key

**aws_region**
- **Type**: Text Field
- **Visible When**: always
- **Required When**: always
- **Validation**:
  - Must be a non-empty string
  - Should match a valid AWS region identifier format (e.g., `us-east-1`)
- **Purpose**: Specifies the AWS region where the target S3 bucket resides
- **Example**: `us-east-1`

**bucket_name**
- **Type**: Text Field
- **Visible When**: always
- **Required When**: always
- **Validation**:
  - Must be a non-empty string
- **Purpose**: Specifies the name of the AWS S3 bucket to operate on
- **Example**: `my-demo-bucket`

**local_file**
- **Type**: Text Field
- **Visible When**: action value is equal to "Upload File". It is required when visible.
- **Required When**: action value is equal to "Upload File"
- **Validation**:
  - Must be a non-empty string representing an absolute path
- **Purpose**: Absolute path to the local file on the Universal Agent host to be uploaded to S3
- **Example**: `/data/reports/file.csv`

**s3_object_key**
- **Type**: Text Field
- **Visible When**: action value is equal to "Upload File". It is required when visible.
- **Required When**: action value is equal to "Upload File"
- **Validation**:
  - Must be a non-empty string
- **Purpose**: Target S3 object key (path and filename) within the bucket where the file will be stored
- **Example**: `data/reports/file.csv`

---

## 2. Output Fields

**status**
- **Type**: Text Output
- **Purpose**: Short human-readable summary of the operation outcome, populated by the extension at completion
- **Examples**: `"Listed 42 objects"`, `"Upload successful"`

**result**
- **Type**: Text Output
- **Purpose**: Key result identifier — the object count string for List Objects, or the full S3 URI for Upload File
- **Examples**: `"42 objects in my-demo-bucket"`, `"s3://my-demo-bucket/data/reports/file.csv"`

---

## 3. Field Ordering

The task form uses a **2-column grid layout**. Fields can be displayed in two ways:

- **Full-width fields**: Span both columns (typically for dropdowns, credentials, or primary selections)
- **Half-width fields**: Occupy one column, allowing two fields side-by-side (typically for related pairs)

**Layout Rules:**
- Credential fields ALWAYS span full-width (both columns)
- Group related fields side-by-side when logical (e.g., country/city, latitude/longitude)
- Primary selection fields typically span full-width for prominence

**Field Order (Visual Layout):**

```
┌─────────────────────────────────────────┐
│                  action                 │  ← Full-width (action selection)
├─────────────────────────────────────────┤
│              aws_credentials            │  ← Full-width (credential — always full-width)
├─────────────────────────────────────────┤
│    aws_region      │    bucket_name     │  ← Half-width pair (related connection fields)
├─────────────────────┼───────────────────┤
│              local_file                 │  ← Full-width (shown only when Upload File)
├─────────────────────────────────────────┤
│             s3_object_key               │  ← Full-width (shown only when Upload File)
├─────────────────────────────────────────┤
│                 status                  │  ← Full-width (output only)
├─────────────────────────────────────────┤
│                 result                  │  ← Full-width (output only)
└─────────────────────────────────────────┘
```

---

# Actions

## Action 1: List Objects

**Description**: Lists all objects in the specified S3 bucket using the `list_objects_v2` API. Displays Key, Size (bytes), and Last Modified for each object in an ASCII table on STDOUT. Output is capped by the `UE_MAX_OUTPUT_RECORDS` environment variable (default: 100). When truncated, a notice is written to STDOUT, STDERR, and the Extension Output metadata. Output-only fields are populated with the count and bucket summary.

### Input Requirements

- **action** — must be "List Objects"
- **aws_credentials** — user: AWS Access Key ID, password: AWS Secret Access Key
- **aws_region** — AWS region of the bucket
- **bucket_name** — S3 bucket to list

### Execution Flow

**Step 1: Read configuration**
- Read `UE_MAX_OUTPUT_RECORDS` from the process environment. If not set or not a valid positive integer, default to `100`. This is the maximum number of objects to include in STDOUT and Extension Output.

**Step 2: Initialize S3 client**
- Create a boto3 S3 client using `aws_credentials.user` as the AWS Access Key ID, `aws_credentials.password` as the AWS Secret Access Key, and `aws_region` as the region name.

**Step 3: Paginate and collect all objects**
- Use the boto3 `list_objects_v2` paginator on `bucket_name` to iterate through all pages. Collect every object's `Key` (string), `Size` (integer, bytes), and `LastModified` (datetime, UTC) into a list. Track `total_count` = total number of objects collected across all pages.

**Step 4: Apply output cap**
- If `total_count` > `max_records`:
  - Set `truncated = True`
  - Slice the collected objects list to the first `max_records` entries
  - Write a warning to STDERR: `"Output truncated: showing {max_records} of {total_count} objects in bucket '{bucket_name}'"`
- Otherwise:
  - Set `truncated = False`

**Step 5: Format LastModified timestamps**
- For each object in the (possibly sliced) list, convert `LastModified` to an ISO 8601 UTC string (e.g., `"2026-09-15T10:30:00+00:00"`).

**Step 6: Build ASCII table**
- Use `tabulate` with `tablefmt="rounded_outline"` to format the objects as a table with three columns: `Key`, `Size (bytes)`, `Last Modified`.
- Print the table to STDOUT.
- If `truncated` is True, print the following notice to STDOUT immediately after the table:
  `"[Truncated] Showing {max_records} of {total_count} objects. Set UE_MAX_OUTPUT_RECORDS to increase the limit."`

**Step 7: Populate output-only fields**
- Set `output_data.status` = `"Listed {len(objects)} objects"` (where `len(objects)` is the number returned, after capping)
- Set `output_data.result` = `"{len(objects)} objects in {bucket_name}"`

**Step 8: Return Extension Output JSON**
- Return a result object containing `object_count` (integer — count of objects returned), `objects` (array of objects with `key`, `size_bytes`, `last_modified`), and — only when truncated — `truncated: true` and `total_count` (integer — total objects in the bucket).

### Output Examples

**STDOUT**:
```
╭──────────────────────────────┬──────────────┬──────────────────────────────╮
│ Key                          │ Size (bytes) │ Last Modified                │
├──────────────────────────────┼──────────────┼──────────────────────────────┤
│ data/file1.csv               │         1024 │ 2026-09-15T10:30:00+00:00    │
│ data/file2.json              │          512 │ 2026-09-20T08:15:00+00:00    │
╰──────────────────────────────┴──────────────┴──────────────────────────────╯
```

When truncated:
```
╭──────────────────────────────┬──────────────┬──────────────────────────────╮
│ Key                          │ Size (bytes) │ Last Modified                │
├──────────────────────────────┼──────────────┼──────────────────────────────┤
│ ...                          │          ... │ ...                          │
╰──────────────────────────────┴──────────────┴──────────────────────────────╯
[Truncated] Showing 100 of 350 objects. Set UE_MAX_OUTPUT_RECORDS to increase the limit.
```

**Extension Output result object (JSON)**:

```json
{
  "result": {
    "object_count": 2,
    "objects": [
      {
        "key": "data/file1.csv",
        "size_bytes": 1024,
        "last_modified": "2026-09-15T10:30:00+00:00"
      },
      {
        "key": "data/file2.json",
        "size_bytes": 512,
        "last_modified": "2026-09-20T08:15:00+00:00"
      }
    ]
  }
}
```

When truncated, include additional fields in the result:
```json
{
  "result": {
    "object_count": 100,
    "objects": ["..."],
    "truncated": true,
    "total_count": 350
  }
}
```

### Success Criteria

1. The `list_objects_v2` paginator completes without a boto3 exception.
2. Object metadata (Key, Size, LastModified) is retrieved and formatted correctly.
3. STDOUT contains the ASCII table with rounded_outline format.
4. Extension Output JSON is populated with `object_count` and `objects` array.
5. When truncated, STDOUT contains the truncation notice, STDERR contains the warning, and Extension Output contains `truncated: true` and `total_count`.
6. Output-only `status` field is set to `"Listed N objects"` and `result` field is set to `"N objects in <bucket>"`.

---

## Action 2: Upload File

**Description**: Uploads a local file from the Universal Agent host filesystem to the specified S3 bucket and key. Validates that the local file exists before making any AWS API calls. Writes a confirmation to STDOUT and returns the S3 URI, bucket, key, and ETag in the Extension Output JSON.

### Input Requirements

- **action** — must be "Upload File"
- **aws_credentials** — user: AWS Access Key ID, password: AWS Secret Access Key
- **aws_region** — AWS region of the bucket
- **bucket_name** — S3 bucket destination
- **local_file** — absolute path to the local file on the agent host
- **s3_object_key** — target key within the bucket

### Execution Flow

**Step 1: Validate local file**
- Check whether the path specified in `local_file` exists and is a file on the agent host filesystem.
- If the file does not exist, raise a ValidationError with status description `"Validation Error: Local file <local_file> not found"` and exit code `20`. Do not proceed further.

**Step 2: Initialize S3 client**
- Create a boto3 S3 client using `aws_credentials.user` as the AWS Access Key ID, `aws_credentials.password` as the AWS Secret Access Key, and `aws_region` as the region name.

**Step 3: Upload the file**
- Use boto3's `upload_file` method to upload `local_file` to `bucket_name` at key `s3_object_key`.

**Step 4: Retrieve the ETag**
- After a successful upload, call `head_object` on `bucket_name` with the `s3_object_key` to retrieve the ETag.
- Strip any surrounding double-quote characters from the ETag string (S3 returns ETags wrapped in quotes, e.g., `"d41d8cd98f00b204e9800998ecf8427e"` → `d41d8cd98f00b204e9800998ecf8427e`).

**Step 5: Write STDOUT confirmation**
- Print to STDOUT: `"Uploaded {local_file} to s3://{bucket_name}/{s3_object_key}"`

**Step 6: Populate output-only fields**
- Set `output_data.status` = `"Upload successful"`
- Set `output_data.result` = `"s3://{bucket_name}/{s3_object_key}"`

**Step 7: Return Extension Output JSON**
- Return a result object with `s3_uri`, `bucket`, `key`, and `etag`.

### Output Examples

**STDOUT**:
```
Uploaded /data/reports/file.csv to s3://my-demo-bucket/data/reports/file.csv
```

**Extension Output result object (JSON)**:

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

### Success Criteria

1. The local file exists and is readable on the agent host (pre-flight validation passes).
2. The boto3 `upload_file` call completes without exception.
3. ETag is retrieved from the `head_object` response.
4. STDOUT contains the confirmation message in the exact format specified.
5. Extension Output JSON is populated with `s3_uri`, `bucket`, `key`, and `etag`.
6. Output-only `status` field is set to `"Upload successful"` and `result` field is set to the full S3 URI.

---

# Progress Reporting

Progress Reporting (percentage of completion report) is not required. Basic informational messages are written to STDOUT during execution (e.g., table output, upload confirmation), but no progress bar is implemented.

---

# Dynamic Choice Field Population

No Dynamic choice fields should be implemented.

---

# Cancellation Behavior

Standard UAC default cancellation logic is used (TERM signal). No special cleanup logic is required. The boto3 client does not hold persistent resources that require explicit teardown.

---

# Re-Run Behavior

Re-runs are treated as initial executions for both actions. Re-running a List Objects task re-queries the bucket. Re-running an Upload File task re-uploads the file, overwriting any existing S3 object at the same key. No special re-run detection or divergent logic is required.

---

# Dynamic Commands

No Dynamic commands should be implemented.

---

# Utility Modules

## Required Utility Modules

### 1. S3ClientUtility

**Purpose:** Encapsulates all AWS S3 API interactions — client initialization, object listing via paginator, file upload, ETag retrieval, and boto3 exception classification into typed extension exceptions.

**Required Capabilities:**

**Client Initialization:**
- Accept AWS Access Key ID, AWS Secret Access Key, and region name as parameters
- Create and return a boto3 S3 client configured with the provided static credentials and region

**Object Listing:**
- Accept a bucket name and a maximum record limit as parameters
- Use the boto3 `list_objects_v2` paginator to iterate all pages of results for the bucket
- Collect each object's `Key` (string), `Size` (integer), and `LastModified` (datetime UTC) into a list
- Return the full collected list and the total count of all objects in the bucket
- Raise appropriate typed exceptions for any boto3 errors encountered

**File Upload:**
- Accept a local file path, bucket name, and S3 object key as parameters
- Invoke boto3's `upload_file` method to upload the file
- Raise appropriate typed exceptions for any boto3 errors encountered

**ETag Retrieval:**
- Accept a bucket name and S3 object key as parameters
- Call `head_object` and extract the ETag string from the response
- Strip surrounding double-quote characters from the ETag before returning

**Exception Classification:**
- Intercept `botocore.exceptions.ClientError` and classify by error code:
  - Codes `InvalidClientTokenId`, `AuthFailure`, `SignatureDoesNotMatch`, `InvalidAccessKeyId` → `S3AuthenticationError`
  - Code `NoSuchBucket` → `S3BucketNotFoundError`
  - Code `AccessDenied` → `S3AccessDeniedError`
  - Any other `ClientError` during upload → `S3UploadError`
- Intercept `botocore.exceptions.ConnectTimeoutError`, `botocore.exceptions.EndpointConnectionError`, and `botocore.exceptions.ConnectionError` → `S3ConnectionError`
- Intercept `boto3.exceptions.S3UploadFailedError` → `S3UploadError`

**Used By:** List Objects action, Upload File action

---

## Exception Mapping Strategy

**Authentication Errors:**
- Invalid or expired AWS credentials (ClientError codes: `InvalidClientTokenId`, `AuthFailure`, `SignatureDoesNotMatch`, `InvalidAccessKeyId`) → `S3AuthenticationError` (exit code 1, non-transient — requires credential correction)

**S3 Resource Errors:**
- Bucket does not exist or is in a different region (ClientError code: `NoSuchBucket`) → `S3BucketNotFoundError` (exit code 1, non-transient — user configuration error)
- IAM policy does not permit the requested operation (ClientError code: `AccessDenied`) → `S3AccessDeniedError` (exit code 1, non-transient — user configuration/permissions error)

**Network Errors:**
- Connection timeout or DNS failure reaching AWS endpoints (`ConnectTimeoutError`, `EndpointConnectionError`, `ConnectionError`) → `S3ConnectionError` (exit code 1, transient — retry may succeed)

**Upload Errors:**
- File upload interrupted or failed mid-transfer (`S3UploadFailedError` or other ClientError during upload) → `S3UploadError` (exit code 1, potentially transient)

**Validation Errors:**
- Local file does not exist on agent host → `ValidationError` (exit code 20, non-transient — user input error)
- Required field has no value → `ValidationError` (exit code 20, non-transient — user input error)

**Exit Code Guide:**
- Exit code 0: Successful execution
- Exit code 1: Runtime failure (authentication, S3 access, network, upload errors)
- Exit code 20: Validation error (missing required fields, local file not found)

---

# Dependencies

## 1. External API Dependencies

**1. AWS S3 (Simple Storage Service)**
- **Endpoint**: `https://s3.<region>.amazonaws.com`
- **Purpose**: Object storage operations — listing bucket contents and uploading files
- **Protocol**: HTTPS
- **Method**: GET (list), PUT (upload), HEAD (ETag retrieval) — all invoked via boto3 SDK, not direct HTTP
- **Authentication**: Static AWS IAM credentials (Access Key ID + Secret Access Key) passed directly to the boto3 client at runtime
- **Response Format**: JSON / XML (handled transparently by boto3)
- **Data Retrieved/Sent**: Object keys, sizes, LastModified timestamps (list); file bytes (upload); ETag (head_object response)

**General API Requirements:**
- AWS account with an IAM user or role that has at least `s3:ListBucket` permission for List Objects and `s3:PutObject` permission for Upload File on the target bucket
- Credentials stored in a UAC Credential entity (`user` = Access Key ID, `password` = Secret Access Key)
- No API key activation steps required beyond standard AWS IAM setup

---

## 2. Python version dependency

Python >= 3.11 is required, as specified in the extension metadata.

---

## 3. Target Platform

Linux (x86_64). C extension modules with a confirmed `manylinux_2_17_x86_64` wheel are viable. All selected dependencies (`boto3`, `tabulate`) are pure-Python, so this constraint does not restrict module selection here.

---

## 4. Python Library Dependencies

**1. boto3**
- **Purpose**: Official AWS SDK for Python; provides all S3 operations (list_objects_v2 paginator, upload_file, head_object, ClientError exception hierarchy)
- **Version**: `1.43.108` (pinned)
- **Installation**: `pip install boto3==1.43.108`
- **Usage**: Instantiating the S3 client, paginating object listings, uploading files, retrieving object metadata
- **Features Used**: `boto3.client('s3')`, `client.get_paginator('list_objects_v2')`, `client.upload_file()`, `client.head_object()`, `botocore.exceptions.ClientError`

**2. tabulate**
- **Purpose**: ASCII table formatter for STDOUT display of S3 object listings
- **Version**: `0.10.0` (pinned)
- **Installation**: `pip install tabulate==0.10.0`
- **Usage**: List Objects action — formats the collected objects list as a human-readable table
- **Features Used**: `tabulate(data, headers, tablefmt="rounded_outline")`

---

## 5. Python Standard Library Dependencies

**1. os**
- **Purpose**: Access environment variables and file system path checks
- **Version**: Standard library (Python 3.11+)
- **Installation**: Built-in — no installation required
- **Usage**: `os.environ.get('UE_MAX_OUTPUT_RECORDS', '100')` for reading the output cap; `os.path.isfile()` for local file existence validation
- **Features Used**: `os.environ.get`, `os.path.isfile`

---

## 6. CLI Tool Dependencies

No Dependencies.

---

## 7. Environment Variables

**UE_MAX_OUTPUT_RECORDS** (*string representing a positive integer*, *optional*):
- **Purpose**: Controls the maximum number of S3 objects included in STDOUT and Extension Output for the List Objects action. Acts as a safety net to prevent large bucket listings from bloating UAC database storage.
- **Default**: `100`
- **Usage**: Read at the start of the List Objects execution flow. If not set or not a valid positive integer, defaults to `100`. Does not affect the Upload File action.
- **Examples**: `50`, `200`, `500`

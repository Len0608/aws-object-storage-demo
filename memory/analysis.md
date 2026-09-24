# AWS Object Storage Demo - Implementation Analysis

**Extension Name:** *AWS Object Storage Demo (aws-object-storage-demo)*
**Universal Template Name:** *Aws Object Storage Demo*
**Target Platform:** Linux

---

## Extension Overview

A minimal MVP Universal Extension that demonstrates AWS S3 integration with Stonebranch UAC using the boto3 SDK bundled entirely within the extension package. The extension exposes two operations — **List Objects** and **Upload File** — authenticated via a UAC Credential Field. All dependencies are pure-Python and require no pre-installation on the agent host.

---

# Template Fields

## 1. Input Fields

**action**
- **Type**: Choice Field (Single-select)
- **Visible When**: always
- **Required When**: always
- **Options**:
  - `List Objects` — Retrieves and displays objects stored in the specified S3 bucket
  - `Upload File` — Uploads a local file from the agent host to the specified S3 bucket
- **Default Value**: `List Objects`
- **Validation**:
  - Must be one of the defined options
- **Purpose**: Selects the S3 operation to perform; controls visibility of action-specific fields

---

**aws_credentials**
- **Type**: Credential Field
- **Visible When**: always
- **Required When**: always
- **Validation**:
  - Must reference a valid UAC Credential entity
  - The `user` attribute of the credential must contain the AWS Access Key ID
  - The `password` attribute of the credential must contain the AWS Secret Access Key
- **Purpose**: Provides AWS authentication for all S3 API calls. Access Key ID is read from `credentials["user"]`; Secret Access Key is read from `credentials["password"]`

---

**aws_region**
- **Type**: Text Field
- **Visible When**: always
- **Required When**: always
- **Validation**:
  - Must not be empty
  - Must be a valid AWS region identifier string (e.g., `us-east-1`, `eu-west-1`)
- **Purpose**: Specifies the AWS region where the target S3 bucket resides; used when creating the boto3 S3 client
- **Example**: `us-east-1`

---

**bucket_name**
- **Type**: Text Field
- **Visible When**: always
- **Required When**: always
- **Validation**:
  - Must not be empty
- **Purpose**: Identifies the target S3 bucket for both List Objects and Upload File operations
- **Example**: `my-demo-bucket`

---

**local_file**
- **Type**: Text Field
- **Visible When**: `action` value is equal to `"Upload File"`. It is required when it's visible
- **Required When**: `action` value is equal to `"Upload File"`
- **Validation**:
  - Must not be empty when visible
  - Must be an absolute filesystem path; validated at runtime before making any S3 API call
- **Purpose**: Full absolute path to the local file on the UAC agent Linux host to be uploaded to S3
- **Example**: `/tmp/reports/q3.csv`

---

**s3_object_key**
- **Type**: Text Field
- **Visible When**: `action` value is equal to `"Upload File"`. It is required when it's visible
- **Required When**: `action` value is equal to `"Upload File"`
- **Validation**:
  - Must not be empty when visible
- **Purpose**: Target object key (path and name) within the S3 bucket that the local file will be stored under
- **Example**: `reports/q3.csv`

---

## 2. Output Fields

**status**
- **Type**: Text Output
- **Purpose**: Brief human-readable result message set on every completion (success or failure). Displayed as a column in the UAC task execution list via `defaultListView: true`
- **Examples**: `"Success: Listed 42 objects in 'my-demo-bucket'"`, `"Success: Uploaded to s3://my-demo-bucket/reports/q3.csv"`, `"Error: Authentication failed — invalid AWS credentials"`

---

**result**
- **Type**: Text Output
- **Purpose**: Action-specific result value set on successful completion. Displayed as a column in the UAC task execution list via `defaultListView: true`
- **Examples**: `"42 objects"` (List Objects), `"s3://my-demo-bucket/reports/q3.csv"` (Upload File)

---

## 3. Field Ordering

The task form uses a **2-column grid layout**.

**Layout Rules:**
- Credential fields ALWAYS span full-width (both columns)
- Text fields containing full filesystem or S3 paths span full-width for readability
- Action selector spans full-width as the primary control
- Output-only fields span full-width

**Field Order (Visual Layout):**

```
┌─────────────────────────────────────────┐
│                  action                  │  ← Full-width
├─────────────────────────────────────────┤
│             aws_credentials             │  ← Full-width (credential)
├─────────────────────────────────────────┤
│               aws_region                │  ← Full-width
├─────────────────────────────────────────┤
│              bucket_name                │  ← Full-width
├─────────────────────────────────────────┤
│              local_file                 │  ← Full-width (Upload File only)
├─────────────────────────────────────────┤
│             s3_object_key               │  ← Full-width (Upload File only)
├─────────────────────────────────────────┤
│               status (output)           │  ← Full-width (output-only)
├─────────────────────────────────────────┤
│               result (output)           │  ← Full-width (output-only)
└─────────────────────────────────────────┘
```

---

# Actions

## Action 1: List Objects

**Description**: Lists objects stored in the specified S3 bucket. Retrieves Key, Size (bytes), and Last Modified (ISO 8601) for each object. Output is capped at `UE_MAX_OUTPUT_RECORDS` (default 100). Results are printed as an ASCII table to STDOUT. If the bucket contains more objects than the cap, the output is marked as truncated with the total object count reported.

### Input Requirements

- **action** (value: `"List Objects"`)
- **aws_credentials** (user = AWS Access Key ID, password = AWS Secret Access Key)
- **aws_region**
- **bucket_name**

### Execution Flow

**Step 1: Input Validation**
- Verify `aws_credentials` is not None; if None, raise `ValidationError` with message `"AWS credentials are required"`
- Verify `aws_region` is not empty; if empty, raise `ValidationError` with message `"AWS region is required"`
- Verify `bucket_name` is not empty; if empty, raise `ValidationError` with message `"Bucket name is required"`

**Step 2: Read Cap Configuration**
- Read environment variable `UE_MAX_OUTPUT_RECORDS`; parse as integer; if not set or not a valid integer, default to `100`
- Assign result to `max_records`

**Step 3: Create S3 Client**
- Instantiate a boto3 S3 client using:
  - `region_name` = `aws_region`
  - `aws_access_key_id` = `aws_credentials["user"]`
  - `aws_secret_access_key` = `aws_credentials["password"]`

**Step 4: Paginate and Collect All Objects**
- Use `list_objects_v2` with pagination (ContinuationToken) to iterate through all pages of objects in `bucket_name`
- For each object encountered:
  - Increment `total_count`
  - If `len(display_list) < max_records`, append `{"key": obj.Key, "size": obj.Size, "last_modified": obj.LastModified.strftime("%Y-%m-%dT%H:%M:%SZ")}` to `display_list`
- Continue paginating until `IsTruncated` is False in the S3 response
- After iteration: `truncated = (total_count > max_records)`

**Step 5: Format and Print STDOUT Table**
- Use `tabulate` to format `display_list` as a table with:
  - `tablefmt="rounded_outline"`
  - Column headers: `Key`, `Size`, `Last Modified`
  - Columns map to `key`, `size`, `last_modified` keys of each dict
- Print the formatted table to STDOUT
- If `truncated` is True, print the following line after the table:
  `"Note: Output limited to <max_records> records. Total objects in bucket: <total_count>."`

**Step 6: Set Output Fields**
- Set `output_data.status` = `"Success: Listed <len(display_list)> objects in '<bucket_name>'"`
- Set `output_data.result` = `"<len(display_list)> objects"`

**Step 7: Build and Return Extension Output**
- Return extension output with `result`:
  ```json
  {
    "objects": [<display_list items>],
    "truncated": <true|false>,
    "total_returned": <total_count>
  }
  ```
- Return exit code `0`

### Output Examples

**STDOUT (not truncated, 2 objects):**
```
╭───────────────────┬───────┬──────────────────────╮
│ Key               │  Size │ Last Modified        │
├───────────────────┼───────┼──────────────────────┤
│ reports/q3.csv    │ 12345 │ 2026-09-24T10:00:00Z │
│ data/input.csv    │ 67890 │ 2026-09-23T08:30:00Z │
╰───────────────────┴───────┴──────────────────────╯
```

**STDOUT (truncated, 2847 total, cap 100):**
```
╭───────────────────┬───────┬──────────────────────╮
│ Key               │  Size │ Last Modified        │
├───────────────────┼───────┼──────────────────────┤
│ reports/q3.csv    │ 12345 │ 2026-09-24T10:00:00Z │
│ ...               │  ...  │ ...                  │
╰───────────────────┴───────┴──────────────────────╯
Note: Output limited to 100 records. Total objects in bucket: 2847.
```

**Extension Output result object (JSON):**

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

*(Note: Extension Output also contains `exit_code`, `status_description`, and `invocation` elements added automatically during implementation time.)*

### Success Criteria
1. boto3 `list_objects_v2` completes without raising an exception
2. STDOUT contains a `rounded_outline` ASCII table with columns Key, Size, Last Modified
3. If `total_count > max_records`: STDOUT ends with a truncation note; Extension Output includes `"truncated": true` and `"total_returned": <total_count>`
4. If `total_count <= max_records`: Extension Output includes `"truncated": false` and `"total_returned": <total_count>`
5. `output_data.status` = `"Success: Listed <N> objects in '<bucket_name>'"`
6. `output_data.result` = `"<N> objects"`
7. Return code = `0`

---

## Action 2: Upload File

**Description**: Uploads a local file from the UAC agent's Linux filesystem to the specified S3 bucket under the given object key. Validates that the local file exists before making any S3 API call. On success, prints the full S3 URI to STDOUT and sets output fields.

### Input Requirements

- **action** (value: `"Upload File"`)
- **aws_credentials** (user = AWS Access Key ID, password = AWS Secret Access Key)
- **aws_region**
- **bucket_name**
- **local_file**
- **s3_object_key**

### Execution Flow

**Step 1: Input Validation**
- Verify `aws_credentials` is not None; if None, raise `ValidationError` with message `"AWS credentials are required"`
- Verify `aws_region` is not empty; if empty, raise `ValidationError` with message `"AWS region is required"`
- Verify `bucket_name` is not empty; if empty, raise `ValidationError` with message `"Bucket name is required"`
- Verify `local_file` is not empty; if empty, raise `ValidationError` with message `"Local file path is required"`
- Verify `s3_object_key` is not empty; if empty, raise `ValidationError` with message `"S3 object key is required"`

**Step 2: Validate Local File Existence**
- Check if the file at path `local_file` exists on the agent filesystem
- If the file does not exist, raise `LocalFileNotFoundError` with message `"Error: Local file not found: '<local_file>'"`

**Step 3: Create S3 Client**
- Instantiate a boto3 S3 client using:
  - `region_name` = `aws_region`
  - `aws_access_key_id` = `aws_credentials["user"]`
  - `aws_secret_access_key` = `aws_credentials["password"]`

**Step 4: Upload File**
- Call `s3_client.upload_file(local_file, bucket_name, s3_object_key)` to upload the local file to S3
- Construct `s3_uri` = `"s3://<bucket_name>/<s3_object_key>"`

**Step 5: Print Confirmation to STDOUT**
- Print: `"Uploaded <local_file> to <s3_uri>"`

**Step 6: Set Output Fields**
- Set `output_data.status` = `"Success: Uploaded to <s3_uri>"`
- Set `output_data.result` = `"<s3_uri>"`

**Step 7: Build and Return Extension Output**
- Return extension output with `result`:
  ```json
  {
    "s3_uri": "<s3_uri>"
  }
  ```
- Return exit code `0`

### Output Examples

**STDOUT:**
```
Uploaded /tmp/reports/q3.csv to s3://my-demo-bucket/reports/q3.csv
```

**Extension Output result object (JSON):**

```json
{
  "result": {
    "s3_uri": "s3://my-demo-bucket/reports/q3.csv"
  }
}
```

*(Note: Extension Output also contains `exit_code`, `status_description`, and `invocation` elements added automatically during implementation time.)*

### Success Criteria
1. The local file exists at the specified path (pre-upload validation passes)
2. boto3 `upload_file` completes without raising an exception
3. STDOUT contains the confirmation line with the full S3 URI
4. `output_data.status` = `"Success: Uploaded to s3://<bucket_name>/<s3_object_key>"`
5. `output_data.result` = `"s3://<bucket_name>/<s3_object_key>"`
6. Extension Output `result.s3_uri` = `"s3://<bucket_name>/<s3_object_key>"`
7. Return code = `0`

---

# Progress Reporting

Progress Reporting (percentage of completion report) is not required. STDOUT output written during execution serves as the visible progress log in the UAC task execution detail.

---

# Dynamic Choice Field Population

No Dynamic choice fields should be implemented.

---

# Cancellation Behavior

Standard UAC task cancellation behavior applies (TERM signal). No special cancellation handling is required by this extension. The extension does not create temporary files or hold persistent connections that require explicit cleanup; ephemeral boto3 client objects are released when the process terminates.

---

# Re-Run Behavior

Re-runs are treated as initial executions for both actions.

- Re-running **List Objects** re-queries S3 at the time of re-run, returning current bucket contents.
- Re-running **Upload File** re-uploads the same local file to the same S3 object key, silently overwriting any existing object at that key. No special re-run detection logic is required.

---

# Dynamic Commands

No Dynamic commands should be implemented.

---

# Utility Modules

## Required Utility Modules

### 1. S3ClientManager

**Purpose:** Encapsulates all boto3 S3 interactions — client creation and the two S3 operations (list objects with pagination, file upload).

**Required Capabilities:**

**Client Creation:**
- Accept `aws_access_key_id` (str), `aws_secret_access_key` (str), and `region_name` (str) as parameters
- Return a configured boto3 S3 client authenticated with the provided explicit credentials

**List Objects (Paginated):**
- Accept `s3_client`, `bucket_name` (str), and `max_records` (int) as parameters
- Paginate through all pages of `list_objects_v2` results using ContinuationToken
- Collect the first `max_records` objects into `display_list` as dicts with keys `key`, `size`, `last_modified` (ISO 8601 string in format `%Y-%m-%dT%H:%M:%SZ`)
- Count ALL objects across all pages into `total_count`
- Return `(display_list, total_count)` tuple
- Propagate boto3 `ClientError` exceptions to the caller without catching them (caller handles error classification)

**Upload File:**
- Accept `s3_client`, `local_file` (str), `bucket_name` (str), and `s3_object_key` (str) as parameters
- Call boto3 `upload_file(local_file, bucket_name, s3_object_key)`
- Propagate boto3 `ClientError` exceptions to the caller without catching them

**Used By:** List Objects action, Upload File action

---

### 2. OutputFormatter

**Purpose:** Formats the List Objects display data as a human-readable ASCII table for STDOUT output.

**Required Capabilities:**

**Table Formatting:**
- Accept a list of object dicts (each with `key`, `size`, `last_modified` keys) as input
- Produce a `tabulate` ASCII table using `tablefmt="rounded_outline"` with column headers: `Key`, `Size`, `Last Modified`
- Return the formatted table string

**Truncation Note:**
- Accept `max_records` (int) and `total_count` (int) as parameters
- Return the truncation note string: `"Note: Output limited to <max_records> records. Total objects in bucket: <total_count>."`

**Used By:** List Objects action

---

## Exception Mapping Strategy

**Validation Errors:**
- Any required field is empty or missing → `ValidationError` (exit code 20, user input error, non-transient)

**AWS Authentication Errors:**
- boto3 `ClientError` with error code `InvalidClientTokenId` or `AuthFailure` → `AuthenticationError` (exit code 1, user configuration error, non-transient)
- boto3 `ClientError` with error code `SignatureDoesNotMatch` → `AuthenticationError` (exit code 1, user configuration error, non-transient)

**AWS Resource Errors:**
- boto3 `ClientError` with error code `NoSuchBucket` → `BucketNotFoundError` (exit code 1, user configuration error, non-transient)
- Local file path does not exist on agent filesystem → `LocalFileNotFoundError` (exit code 1, user input error, non-transient)

**AWS Permission Errors:**
- boto3 `ClientError` with error code `AccessDenied` → `PermissionDeniedError` (exit code 1, user configuration error, non-transient)

**Network / Connectivity Errors:**
- `EndpointConnectionError`, `ConnectTimeoutError`, or any connection-related exception from boto3/botocore → `NetworkError` (exit code 1, transient)

**Unhandled Exceptions:**
- Any unexpected exception type not covered above → caught at top-level dispatcher, set `output_data.status` to a generic error message, return exit code 1

**Status Description Patterns (set on `output_data.status` for all error cases):**
- `AuthenticationError` → `"Error: Authentication failed — invalid AWS credentials"`
- `BucketNotFoundError` → `"Error: Bucket '<bucket_name>' not found or not accessible"`
- `LocalFileNotFoundError` → `"Error: Local file not found: '<local_file>'"`
- `PermissionDeniedError` → `"Error: Permission denied for operation on '<bucket_name>'"`
- `NetworkError` → `"Error: Network error — cannot connect to S3"`
- `ValidationError` → `"Validation Error: <field-specific message>"`

**Exit Code Guide:**
- Exit code 0: Successful execution
- Exit code 1: All failure scenarios (authentication, resource, permission, network, unhandled)
- Exit code 20: Input validation error (field empty or missing)

---

# Dependencies

## 1. External API Dependencies

**1. Amazon S3 (AWS Simple Storage Service)**
- **Endpoint**: `https://s3.<region>.amazonaws.com` (resolved automatically by boto3 based on `region_name`)
- **Purpose**: Cloud object storage — source of object listings and destination for file uploads
- **Protocol**: HTTPS
- **Method**: Multiple (GET for list, PUT for upload — managed transparently by boto3)
- **Authentication**: AWS Signature Version 4 via explicit `aws_access_key_id` and `aws_secret_access_key` passed to boto3 client constructor
- **Response Format**: XML (parsed transparently by boto3 into Python dicts)
- **Data Retrieved/Sent**: Object metadata (Key, Size, LastModified) for list; binary file content for upload

**General API Requirements:**
- A valid AWS account with S3 access is required
- The IAM user associated with the Access Key ID must have `s3:ListBucket` permission for List Objects and `s3:PutObject` permission for Upload File on the target bucket
- No API key registration step is needed beyond creating the IAM user and generating an Access Key pair in the AWS Console

---

## 2. Python version dependency

Python >= 3.11, as configured in the workspace environment.

---

## 3. Target Platform

Linux x86_64. C extension modules with a confirmed `manylinux_2_17_x86_64` wheel are viable in addition to pure-Python modules. Both `boto3` and `tabulate` are pure-Python packages, so no binary wheel constraints apply.

---

## 4. Python Library Dependencies

**1. boto3**
- **Purpose**: AWS SDK for Python; provides all required S3 operations (`list_objects_v2` with pagination, `upload_file`)
- **Version**: `1.43.101`
- **Installation**: `pip install boto3==1.43.101`
- **Usage**: Used in `S3ClientManager` utility module for S3 client creation, paginated object listing, and file upload
- **Features Used**: `boto3.client("s3", ...)`, `client.list_objects_v2(...)`, `client.upload_file(...)`, `client.get_paginator("list_objects_v2")`

**2. tabulate**
- **Purpose**: Pure-Python ASCII table formatting library for STDOUT output in the List Objects action
- **Version**: `0.10.0`
- **Installation**: `pip install tabulate==0.10.0`
- **Usage**: Used in `OutputFormatter` utility module to render the object list as a `rounded_outline` ASCII table
- **Features Used**: `tabulate(data, headers=..., tablefmt="rounded_outline")`

---

## 5. Python Standard Library Dependencies

**1. os**
- **Purpose**: Filesystem interaction
- **Version**: Standard library (Python 3.11+)
- **Installation**: Built-in, no installation required
- **Usage**: Check local file existence (`os.path.isfile`) before Upload File S3 call; read environment variable `UE_MAX_OUTPUT_RECORDS` (`os.environ.get`)
- **Features Used**: `os.path.isfile`, `os.environ.get`

**2. logging**
- **Purpose**: STDERR logging at configurable log levels (INFO, DEBUG)
- **Version**: Standard library (Python 3.11+)
- **Installation**: Built-in, no installation required
- **Usage**: Log debug information, error details, and exception stack traces via STDERR
- **Features Used**: `logging.getLogger`, `logger.info`, `logger.debug`, `logger.error`, `logger.exception`

---

## 6. CLI Tool Dependencies

No Dependencies.

---

## 7. Environment Variables

**UE_MAX_OUTPUT_RECORDS** (*integer*, *optional*):
- **Purpose**: Caps the number of S3 objects included in the List Objects STDOUT table and Extension Output JSON. Acts as a safety net to prevent large datasets from bloating UAC database storage
- **Default**: `100`
- **Usage**: Read at the start of the List Objects action execution; parsed as integer; falls back to `100` if not set or not a valid integer value
- **Examples**: `50`, `100`, `500`

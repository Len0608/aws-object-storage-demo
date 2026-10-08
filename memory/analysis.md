# AWS Object Storage - Implementation Analysis

**Extension Name:** *AWS Object Storage (aws-object-storage-demo)*
**Universal Template Name:** *Aws Object Storage Demo*
**Target Platform:** Linux

---

## Extension Overview

The AWS Object Storage extension provides a minimal, demo-grade integration with Amazon S3. It enables UAC tasks to list objects in an S3 bucket (displaying Key, Size, and Last Modified in a formatted ASCII table) and upload local files from the Universal Agent host to a specified S3 bucket and key. Authentication uses AWS Access Key ID and Secret Access Key passed via a UAC Credential field. All boto3-based dependencies are pure-Python and bundled with the extension.

---

# Template Fields

## 1. Input Fields

**action**
- **Type**: Choice Field (Single-select)
- **Visible When**: always
- **Required When**: always
- **Options**:
  - `List Objects` - Lists objects in the specified S3 bucket, displaying Key, Size (B), and Last Modified
  - `Upload File` - Uploads a local file from the agent host to a specified S3 bucket and key
- **Default Value**: `List Objects`
- **Validation**:
  - Must be one of the defined options
- **Purpose**: Selects the S3 operation to perform

---

**aws_credentials**
- **Type**: Credential Field
- **Visible When**: always
- **Required When**: always
- **Validation**:
  - Must reference a valid UAC Credential record
  - `user` attribute must contain the AWS Access Key ID
  - `password` attribute must contain the AWS Secret Access Key
- **Purpose**: Provides AWS authentication. The `user` attribute maps to AWS Access Key ID; the `password` attribute maps to AWS Secret Access Key

---

**aws_region**
- **Type**: Text Field
- **Visible When**: always
- **Required When**: always
- **Default Value**: `us-east-1`
- **Validation**:
  - Must be a non-empty string
  - Must match the AWS region identifier format (e.g., `us-east-1`, `eu-west-1`)
- **Purpose**: Specifies the AWS region where the target S3 bucket resides
- **Example**: `us-east-1`

---

**bucket_name**
- **Type**: Text Field
- **Visible When**: always
- **Required When**: always
- **Validation**:
  - Must be a non-empty string
  - Must be a valid S3 bucket name
- **Purpose**: The name of the S3 bucket to operate on
- **Example**: `my-demo-bucket`

---

**local_file**
- **Type**: Text Field
- **Visible When**: action value is equal to `Upload File`. It is required when it's visible
- **Required When**: action value is equal to `Upload File`
- **Validation**:
  - Must be a non-empty string when visible
  - Must be an absolute file path
- **Purpose**: Absolute path to the local file on the Universal Agent host to be uploaded to S3
- **Example**: `/tmp/reports/jan-2026.csv`

---

**s3_object_key**
- **Type**: Text Field
- **Visible When**: action value is equal to `Upload File`. It is required when it's visible
- **Required When**: action value is equal to `Upload File`
- **Validation**:
  - Must be a non-empty string when visible
- **Purpose**: Destination object key (path and filename) within the S3 bucket
- **Example**: `reports/jan-2026.csv`

---

## 2. Output Fields

**result_summary**
- **Type**: Text Output
- **Purpose**: A short result summary string populated at runtime after action execution
- **Examples**: `"42 objects found in bucket"`, `"Uploaded: s3://my-demo-bucket/reports/jan-2026.csv"`

---

## 3. Field Ordering

The task form uses a **2-column grid layout**.

**Field Order (Visual Layout):**

```
┌─────────────────────────────────────────┐
│                  action                 │  ← Full-width
├─────────────────────────────────────────┤
│              aws_credentials            │  ← Full-width (credential)
├─────────────────────────────────────────┤
│          aws_region  │   bucket_name    │  ← Half-width pair
├──────────────────────┼──────────────────┤
│          local_file  │  s3_object_key   │  ← Half-width pair (Upload File only)
├─────────────────────────────────────────┤
│               result_summary            │  ← Full-width (output only)
└─────────────────────────────────────────┘
```

---

# Actions

## Action 1: List Objects

**Description**: Connects to AWS S3 and retrieves all objects from the specified bucket. Renders Key, Size (B), and Last Modified in an ASCII table on STDOUT. The number of rows displayed is capped by the `UE_MAX_OUTPUT_RECORDS` environment variable (default 100). Populates the `result_summary` output field with the total object count.

### Input Requirements

- **action** (value: `List Objects`)
- **aws_credentials**
- **aws_region**
- **bucket_name**

### Execution Flow

**Step 1: Input Validation**
- Verify that `aws_credentials`, `aws_region`, and `bucket_name` are provided and non-empty
- If any required field is missing, raise a ValidationError with a descriptive message (exit code 20) before any API call is made

**Step 2: Read Environment Configuration**
- Read the `UE_MAX_OUTPUT_RECORDS` environment variable
- Parse the value as a positive integer; if absent, not a valid integer, or less than 1, default to `100`
- Log the effective cap value to STDERR at INFO level

**Step 3: Establish S3 Client**
- Create a boto3 S3 client using:
  - `aws_access_key_id` = `input_data.aws_credentials.user`
  - `aws_secret_access_key` = `input_data.aws_credentials.password`
  - `region_name` = `input_data.aws_region`
- Print `"Connecting to S3 in region '<aws_region>'"` to STDOUT

**Step 4: Retrieve All Objects**
- Print `"Listing objects in bucket '<bucket_name>'"` to STDOUT
- Call `list_objects_v2` with `Bucket=bucket_name`
- Paginate using `NextContinuationToken` until `IsTruncated` is False
- Collect all objects, each as a record with: `key` (string), `size` (integer, bytes), `last_modified` (ISO 8601 UTC string formatted as `YYYY-MM-DDTHH:MM:SSZ`)
- Count the total number of objects: `total_count`

**Step 5: Apply Output Cap**
- Set `displayed_count` = `min(total_count, max_records)`
- Slice the collected objects list to `max_records` entries for display

**Step 6: Format and Emit STDOUT**
- Build a tabulate table from the sliced objects list with columns: `Key`, `Size (B)`, `Last Modified`
- Render using `tablefmt="rounded_outline"`
- Print the table to STDOUT
- If `displayed_count < total_count`, append the following note to STDOUT: `"Note: Displaying <displayed_count> of <total_count> objects. Set UE_MAX_OUTPUT_RECORDS to increase."`
- Also emit a STDERR WARNING when truncation occurs

**Step 7: Populate Outputs and Return**
- Set `output_data.result_summary` = `"<total_count> objects found in bucket"`
- Set `status_description` = `"Success: Listed <total_count> objects in <bucket_name>"`
- Return Extension Output `result` containing `bucket`, `object_count`, `displayed_count`, and `objects` list (sliced to cap)

### Output Examples

**STDOUT**:
```
Connecting to S3 in region 'us-east-1'
Listing objects in bucket 'my-demo-bucket'
╭───────────────────────────┬──────────┬──────────────────────╮
│ Key                       │ Size (B) │ Last Modified        │
├───────────────────────────┼──────────┼──────────────────────┤
│ reports/jan-2026.csv      │   184320 │ 2026-01-15T09:23:41Z │
│ reports/feb-2026.csv      │   202112 │ 2026-02-10T14:05:22Z │
╰───────────────────────────┴──────────┴──────────────────────╯
```

**Extension Output result object (JSON)**:

```json
{
  "result": {
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
}
```

### Success Criteria

1. boto3 `list_objects_v2` call (including all pagination) completes without raising an exception
2. STDOUT contains the ASCII table with at least the header row
3. `result_summary` output field is set to `"<N> objects found in bucket"`
4. Extension Output JSON is valid and contains `bucket`, `object_count`, `displayed_count`, and `objects`
5. Return code is `0`

---

## Action 2: Upload File

**Description**: Validates that the specified local file exists on the agent host, then uploads it to the designated S3 bucket and key using boto3. Prints a confirmation to STDOUT and populates the `result_summary` output field with the S3 destination path.

### Input Requirements

- **action** (value: `Upload File`)
- **aws_credentials**
- **aws_region**
- **bucket_name**
- **local_file**
- **s3_object_key**

### Execution Flow

**Step 1: Input Validation**
- Verify that `aws_credentials`, `aws_region`, `bucket_name`, `local_file`, and `s3_object_key` are provided and non-empty
- If any required field is missing, raise a ValidationError with a descriptive message (exit code 20) before any filesystem or API call is made

**Step 2: Verify Local File Exists**
- Check whether `local_file` path exists on the filesystem (`os.path.exists`)
- If the file does not exist, raise LocalFileNotFoundError: status description `"Error: Local file not found — <local_file>"`, exit code 1
- Obtain file size in bytes using `os.path.getsize(local_file)`

**Step 3: Establish S3 Client**
- Create a boto3 S3 client using:
  - `aws_access_key_id` = `input_data.aws_credentials.user`
  - `aws_secret_access_key` = `input_data.aws_credentials.password`
  - `region_name` = `input_data.aws_region`
- Print `"Connecting to S3 in region '<aws_region>'"` to STDOUT

**Step 4: Upload File**
- Print `"Uploading '<local_file>' to s3://<bucket_name>/<s3_object_key>'"` to STDOUT
- Call `s3_client.upload_file(local_file, bucket_name, s3_object_key)` using a context-managed file handle pattern to ensure file descriptor release on both success and failure

**Step 5: Populate Outputs and Return**
- Print `"Uploaded: s3://<bucket_name>/<s3_object_key>"` to STDOUT
- Set `output_data.result_summary` = `"Uploaded: s3://<bucket_name>/<s3_object_key>"`
- Set `status_description` = `"Success: File uploaded to s3://<bucket_name>/<s3_object_key>"`
- Return Extension Output `result` containing `bucket`, `key`, and `file_size` (bytes)

### Output Examples

**STDOUT**:
```
Connecting to S3 in region 'us-east-1'
Uploading '/tmp/reports/jan-2026.csv' to s3://my-demo-bucket/reports/jan-2026.csv
Uploaded: s3://my-demo-bucket/reports/jan-2026.csv
```

**Extension Output result object (JSON)**:

```json
{
  "result": {
    "bucket": "my-demo-bucket",
    "key": "reports/jan-2026.csv",
    "file_size": 184320
  }
}
```

### Success Criteria

1. Local file exists at the given path (pre-checked before any S3 call)
2. boto3 `upload_file` call completes without raising an exception
3. STDOUT contains the confirmation line `"Uploaded: s3://<bucket>/<key>"`
4. `result_summary` output field is set to `"Uploaded: s3://<bucket>/<key>"`
5. Extension Output JSON is valid and contains `bucket`, `key`, and `file_size`
6. Return code is `0`

---

# Progress Reporting

Progress Reporting (percentage of completion report) is not required. The extension logs key execution steps to STDOUT (connecting to S3, listing objects, uploading file) so the UAC task log reflects progress without a percentage bar.

---

# Dynamic Choice Field Population

No Dynamic choice fields should be implemented.

---

# Cancellation Behavior

Default cancellation behavior is used (TERM signal). No custom cancellation logic is required. The boto3 S3 client and any open file handles will be released by Python's garbage collector or OS on process termination.

---

# Re-Run Behavior

Re-runs are treated as initial executions. No special state management or previous-run data is required between runs. Each execution performs the full action from scratch.

---

# Dynamic Commands

No Dynamic commands should be implemented.

---

# Utility Modules

## Required Utility Modules

### 1. S3 Client Factory

**Purpose:** Creates and returns a configured boto3 S3 client using the provided credentials and region. Centralises client construction so both actions share identical connection setup.

**Required Capabilities:**
- Accept AWS Access Key ID, AWS Secret Access Key, and region name as parameters
- Construct and return a boto3 `S3Client` instance with those credentials
- Validate that the region string is non-empty before client construction

**Used By:** List Objects action, Upload File action

---

### 2. Object Listing Formatter

**Purpose:** Formats a list of S3 object records for STDOUT display. Applies the output record cap and builds the ASCII table.

**Required Capabilities:**

**Record Capping:**
- Read `UE_MAX_OUTPUT_RECORDS` environment variable; default to `100` if absent or non-integer
- Slice the full object list to the cap limit
- Return both the sliced list and the total count so the caller can determine whether truncation occurred

**Table Rendering:**
- Accept a list of object records (each with `key`, `size`, `last_modified`)
- Format `last_modified` values as ISO 8601 UTC strings (`YYYY-MM-DDTHH:MM:SSZ`)
- Render using `tabulate` with columns `Key`, `Size (B)`, `Last Modified` and `tablefmt="rounded_outline"`
- Return the formatted table string for the caller to print

**Truncation Notice:**
- If the sliced count is less than the total count, return the truncation notice string: `"Note: Displaying <displayed_count> of <total_count> objects. Set UE_MAX_OUTPUT_RECORDS to increase."`

**Used By:** List Objects action

---

### 3. AWS Error Classifier

**Purpose:** Catches boto3/botocore exceptions and translates them into appropriate extension-specific custom exceptions with descriptive messages.

**Required Capabilities:**

**boto3 ClientError Classification:**
- Inspect the error response's `Error.Code` field to determine error category
- Map `InvalidClientTokenId`, `AuthFailure`, `SignatureDoesNotMatch` → `S3AuthenticationError`
- Map `NoSuchBucket` → `S3BucketNotFoundError`
- Map `AccessDenied` on bucket-level operations → `S3BucketNotFoundError` (treated as not accessible)
- Map `InvalidRegion` or endpoint resolution failures → `S3InvalidRegionError`
- Map all other `ClientError` codes during upload → `S3UploadError`
- Map all remaining unclassified errors → `S3OperationError`

**Error Message Construction:**
- Include the AWS error code and AWS error message in the constructed exception message
- Follow the pattern: `"<Category>: <description> — <AWS error message>"`

**Used By:** List Objects action, Upload File action

---

## Exception Mapping Strategy

**Input Validation Errors:**
- Missing or empty required field value → `ValidationError` (exit code 20, user input error)

**Local Filesystem Errors:**
- `local_file` path does not exist → `LocalFileNotFoundError` (exit code 1, user input error)

**AWS Authentication Errors:**
- `InvalidClientTokenId`, `AuthFailure`, `SignatureDoesNotMatch` → `S3AuthenticationError` (exit code 1, user configuration error, non-transient)

**AWS Resource Errors:**
- `NoSuchBucket`, `AccessDenied` (bucket scope) → `S3BucketNotFoundError` (exit code 1, user configuration error, non-transient)

**AWS Region Errors:**
- `InvalidRegion`, endpoint resolution failure → `S3InvalidRegionError` (exit code 1, user configuration error, non-transient)

**AWS Upload Errors:**
- `ClientError` during `upload_file` call (non-auth, non-bucket codes) → `S3UploadError` (exit code 1, may be transient)

**Unexpected AWS Errors:**
- Any other `ClientError` or `BotoCoreError` not matched above → `S3OperationError` (exit code 1, unexpected system error)

**Exit Code Guide:**
- Exit code 0: Successful execution
- Exit code 1: Failed execution (authentication, resource not found, upload failure, unexpected error)
- Exit code 20: Input validation error (missing or invalid field values, detected before any API call)

---

# Dependencies

## 1. External API Dependencies

**1. Amazon S3 API**
- **Endpoint**: `https://s3.<region>.amazonaws.com`
- **Purpose**: List objects in a bucket and upload files to a bucket
- **Protocol**: HTTPS
- **Method**: GET (list), PUT (upload) — invoked internally by boto3; extension does not call the API directly
- **Authentication**: AWS Signature Version 4, derived from AWS Access Key ID and Secret Access Key passed to boto3 S3 client constructor
- **Response Format**: JSON / XML (handled transparently by boto3)
- **Data Retrieved/Sent**: Object metadata (Key, Size, LastModified) for listing; binary file data for upload

**General API Requirements:**
- An active AWS account with an IAM user or role possessing at minimum `s3:ListBucket` (for List Objects) and `s3:PutObject` (for Upload File) permissions on the target bucket
- AWS Access Key ID and Secret Access Key configured in a UAC Credential record

---

## 2. Python version dependency

Python >= 3.11 is required.

---

## 3. Target Platform

Linux (x86_64). C extension modules with a confirmed `manylinux_2_17_x86_64` wheel are viable in addition to pure-Python modules. All dependencies used by this extension are pure-Python, so no wheel compatibility issues arise.

---

## 4. Python Library Dependencies

**1. boto3**
- **Purpose**: AWS SDK for Python; provides the S3 client for listing objects and uploading files
- **Version**: `==1.43.109`
- **Installation**: `pip install boto3==1.43.109`
- **Usage**: Instantiated as an S3 client in the S3 Client Factory utility; `list_objects_v2` for List Objects action, `upload_file` for Upload File action
- **Features Used**: `boto3.client('s3', ...)`, `list_objects_v2`, `upload_file`, paginator support via `NextContinuationToken`

**2. botocore**
- **Purpose**: Core AWS protocol, request signing, and retry logic; required transitive dependency of boto3
- **Version**: `==1.43.109`
- **Installation**: `pip install botocore==1.43.109`
- **Usage**: Provides `botocore.exceptions.ClientError` and `botocore.exceptions.BotoCoreError` for error handling in the AWS Error Classifier utility
- **Features Used**: Exception classes `ClientError`, `BotoCoreError`

**3. s3transfer**
- **Purpose**: Manages multipart S3 transfers; required transitive dependency of boto3, used internally by `upload_file()`
- **Version**: `==0.19.2`
- **Installation**: `pip install s3transfer==0.19.2`
- **Usage**: Used internally by boto3's `upload_file` — no direct usage in extension code
- **Features Used**: Multipart upload management (transparent to extension code)

**4. jmespath**
- **Purpose**: JSON query language library; required transitive dependency of boto3/botocore for response parsing
- **Version**: `==1.1.0`
- **Installation**: `pip install jmespath==1.1.0`
- **Usage**: Used internally by boto3/botocore — no direct usage in extension code
- **Features Used**: Response parsing (transparent to extension code)

**5. tabulate**
- **Purpose**: Formats tabular data as ASCII tables; used to render the S3 object listing on STDOUT
- **Version**: `==0.10.0`
- **Installation**: `pip install tabulate==0.10.0`
- **Usage**: Called in the Object Listing Formatter utility with `tablefmt="rounded_outline"` to produce the object listing table
- **Features Used**: `tabulate(data, headers, tablefmt="rounded_outline")`

---

## 5. Python Standard Library Dependencies

**1. os**
- **Purpose**: Filesystem operations for local file validation and size retrieval
- **Version**: Standard library (Python 3.11+)
- **Installation**: Built-in
- **Usage**: `os.path.exists` to verify `local_file` existence; `os.path.getsize` to obtain file size before upload
- **Features Used**: `os.path.exists`, `os.path.getsize`, `os.environ.get`

**2. datetime**
- **Purpose**: Formatting `LastModified` timestamps from the S3 API response as ISO 8601 UTC strings
- **Version**: Standard library (Python 3.11+)
- **Installation**: Built-in
- **Usage**: Convert boto3-returned datetime objects to `YYYY-MM-DDTHH:MM:SSZ` format strings in the Object Listing Formatter utility
- **Features Used**: `datetime.strftime`, `datetime.astimezone`, `timezone.utc`

---

## 6. CLI Tool Dependencies

No Dependencies.

---

## 7. Environment Variables

**UE_MAX_OUTPUT_RECORDS** (*integer*, *optional*):
- **Purpose**: Controls the maximum number of S3 objects displayed in STDOUT and included in the Extension Output `objects` array for the List Objects action. Objects beyond the limit are counted but not listed inline.
- **Default**: `100`
- **Usage**: Read at the start of the List Objects action by the Object Listing Formatter utility; parsed as a positive integer; invalid or missing values fall back to `100`
- **Examples**: `50`, `200`, `500`

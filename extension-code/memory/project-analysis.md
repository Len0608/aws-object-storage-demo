<!-- generated: 2026-10-06T00:00:00 -->
# Universal Extension — aws-object-storage-demo v1.0.0

## Purpose

Integrates UAC with AWS S3 to list all objects in a bucket or upload a local file from the agent host to a specified S3 bucket and key.

---

## Execution Modes / Actions

| Mode | Trigger | Description |
|------|---------|-------------|
| List Objects | `action` = "List Objects" (default) | Paginates through all objects in the target S3 bucket, prints an ASCII table (Key, Size, Last Modified) to STDOUT, and caps output at `UE_MAX_OUTPUT_RECORDS` (default 100). Populates `status` and `result` output fields. |
| Upload File | `action` = "Upload File" | Validates the local file exists, uploads it to the specified S3 key using boto3, retrieves the ETag, prints confirmation to STDOUT, and populates `status` and `result` output fields with the S3 URI. |

---

## Field Table

| # | Name | Label | Type | Mapping | Required | Default | Visibility | Notes |
|---|------|-------|------|---------|----------|---------|------------|-------|
| 0 | `action` | Action | Choice | Choice Field 1 | No | "List Objects" | Always | Choices: "List Objects", "Upload File". Drives conditional visibility of upload-only fields. |
| 1 | `aws_credentials` | AWS Credentials | Credential | Credential Field 1 | Yes | — | Always | `user` = AWS Access Key ID; `password` = AWS Secret Access Key. `allowVariable=true`. |
| 2 | `aws_region` | AWS Region | Text | Text Field 1 | Yes | — | Always | AWS region string (e.g., `us-east-1`). Column span 1 (left half of row). |
| 3 | `bucket_name` | Bucket Name | Text | Text Field 2 | Yes | — | Always | S3 bucket name (e.g., `my-demo-bucket`). Column span 1 (right half of row). |
| 4 | `local_file` | Local File Path | Text | Text Field 3 | Conditional | — | Only when `action` = "Upload File" | Absolute path on agent host. `requireIfVisible=true`, `noSpaceIfHidden=true`. |
| 5 | `s3_object_key` | S3 Object Key | Text | Text Field 4 | Conditional | — | Only when `action` = "Upload File" | Target key within the bucket (e.g., `data/reports/file.csv`). `requireIfVisible=true`, `noSpaceIfHidden=true`. |
| 6 | `status` | Status | Text (Output Only) | Text Field 5 | No | — | Always | Extension-populated status summary. `extensionStatus=true`, `defaultListView=true`, `preserveOutputOnRerun=true`. |
| 7 | `result` | Result | Text (Output Only) | Text Field 6 | No | — | Always | Extension-populated key result: object count string or full S3 URI. `defaultListView=true`, `preserveOutputOnRerun=true`. |

---

## Cross-References

**Always required**
- `aws_credentials` — required by template and validated in `_validate_aws_credentials()`; both `user` and `password` must be non-empty.
- `aws_region` — required by template and validated in `_validate_aws_region()`; must be non-empty string.
- `bucket_name` — required by template and validated in `_validate_bucket_name()`; must be non-empty string.

**Conditionally required (when `action` = "Upload File")**
- `local_file` — `requireIfVisible=true`; validated in `_validate_local_file()`; must be non-empty when action is Upload File.
- `s3_object_key` — `requireIfVisible=true`; validated in `_validate_s3_object_key()`; must be non-empty when action is Upload File.

**Visibility dependencies**
- `local_file`: shown/hidden based on `showIfField=Choice Field 1`, `showIfFieldValue="Upload File"`.
- `s3_object_key`: shown/hidden based on `showIfField=Choice Field 1`, `showIfFieldValue="Upload File"`.
- Both fields use `noSpaceIfHidden=true` — they collapse entirely when hidden, with no reserved space.

**Mutually exclusive options**
- The two action values are mutually exclusive. "List Objects" ignores `local_file` and `s3_object_key` entirely; "Upload File" requires both.

---

## Error Handling

| Scope | Error | Handling |
|-------|-------|----------|
| Input validation | `DataValidationError` (exit 20) | Raised in `InputFields.__post_init__()` when any field validation fails (invalid action value, missing credential user/password, empty region/bucket, missing `local_file` or `s3_object_key` for Upload File). Errors collected via `ExtensionManager`; single raise at end of validation. |
| Pre-flight file check | `ValidationError` (exit 20) | Raised in `upload_file()` before any AWS API call when the local file path does not exist on the agent host (`os.path.isfile()` returns False). Non-retryable without correcting the path. |
| AWS authentication | `S3AuthenticationError` (exit 1) | Raised on `botocore.exceptions.ClientError` with codes `InvalidClientTokenId`, `AuthFailure`, `SignatureDoesNotMatch`, or `InvalidAccessKeyId`. Credentials in the UAC Credential entity must be corrected. |
| Bucket lookup | `S3BucketNotFoundError` (exit 1) | Raised on `ClientError` with code `NoSuchBucket`. Non-transient — `bucket_name` or `aws_region` field must be corrected. |
| IAM permissions | `S3AccessDeniedError` (exit 1) | Raised on `ClientError` with code `AccessDenied`. IAM user or role policy must be updated to permit the requested operation. |
| Network / connectivity | `S3ConnectionError` (exit 1) | Raised on `ConnectTimeoutError`, `EndpointConnectionError`, or `ConnectionError` from botocore. Potentially transient; retry after connectivity is restored. |
| Upload failure | `S3UploadError` (exit 1) | Raised on `boto3.exceptions.S3UploadFailedError` or a `ClientError` during an upload that does not map to a more specific type. Potentially transient. |
| Unexpected system error | `UnexpectedSystemError` (exit 1) | Caught by the bare `except Exception` in `extension_start()`; wraps any unhandled exception with its `type.__name__` or message for debugging. Always reported to UAC status output. |

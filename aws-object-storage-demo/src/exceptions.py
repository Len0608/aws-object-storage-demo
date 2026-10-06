"""
Exceptions module template for UAC Universal Extensions.

This module provides:
- Base ExecutionError class
- Standard exception types (DataValidationError, ConnectionError, etc.)
- ErrorManager singleton for error collection
- Exit code conventions

CUSTOMIZE:
- Add custom exception types for your extension
- Modify ErrorManager methods if needed
"""
from typing import Optional

class ExecutionError(Exception):
    """
    The default error raised by an extension.

    All extension errors must inherit from it.

    Attrs:
        exit_code: The exit code of the extension (for UAC)
        message: The error message for status description
    """

    exit_code: int = 1
    message: str = "Execution Failed"

    def __init__(self, message: Optional[str] = None):
        """
        Initialize exception.

        Args:
            message: Optional message that will be appended to the default message.

        Note:
            To return result data with errors, use error_manager.set_result()
            before raising the exception.
        """
        if message:
            self.message = f"{self.message}: {message}"

        super().__init__(self.message)

class DataValidationError(ExecutionError):
    """Raised when an input field is invalid."""
    exit_code = 20
    message = "Data Validation Error"

class UnexpectedSystemError(ExecutionError):
    """Raised for unexpected system errors."""
    exit_code = 1
    message = "System Error"

class ValidationError(ExecutionError):
    """
    Raised when user-supplied input fails validation before any external call.

    Use when:
    - A required field value is missing or empty
    - A local file path does not exist on the agent host
    - Any pre-flight input check fails that does not depend on an external service
    """
    exit_code = 20
    message = "Validation Error"

class S3AuthenticationError(ExecutionError):
    """
    Raised when AWS credentials are rejected by the S3 service.

    Use when botocore.exceptions.ClientError is raised with error codes:
    InvalidClientTokenId, AuthFailure, SignatureDoesNotMatch, InvalidAccessKeyId.
    Indicates the credentials stored in the UAC Credential entity are incorrect
    or have been revoked and must be corrected before retrying.
    """
    exit_code = 1
    message = "S3 Authentication Error"

class S3BucketNotFoundError(ExecutionError):
    """
    Raised when the specified S3 bucket does not exist or is in a different region.

    Use when botocore.exceptions.ClientError is raised with error code NoSuchBucket.
    Non-transient — the bucket name or aws_region field must be corrected.
    """
    exit_code = 1
    message = "S3 Bucket Not Found"

class S3AccessDeniedError(ExecutionError):
    """
    Raised when the IAM policy does not permit the requested S3 operation.

    Use when botocore.exceptions.ClientError is raised with error code AccessDenied.
    Non-transient — the IAM user or role permissions must be updated.
    """
    exit_code = 1
    message = "S3 Access Denied"

class S3ConnectionError(ExecutionError):
    """
    Raised when a network-level failure prevents reaching the AWS S3 endpoint.

    Use when any of the following botocore exceptions occur:
    botocore.exceptions.ConnectTimeoutError,
    botocore.exceptions.EndpointConnectionError,
    botocore.exceptions.ConnectionError.
    Potentially transient — a retry may succeed once connectivity is restored.
    """
    exit_code = 1
    message = "S3 Connection Error"

class S3UploadError(ExecutionError):
    """
    Raised when a file upload to S3 fails or is interrupted mid-transfer.

    Use when boto3.exceptions.S3UploadFailedError is raised, or when a
    botocore.exceptions.ClientError occurs specifically during an upload operation
    and does not map to a more specific exception type.
    Potentially transient — the upload may succeed on retry.
    """
    exit_code = 1
    message = "S3 Upload Error"

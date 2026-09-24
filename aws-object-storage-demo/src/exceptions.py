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
    Raised when a required input field is empty or missing.

    Use this when validating that mandatory fields (e.g., aws_region,
    bucket_name, local_file) are not empty before invoking any S3 API call.

    Example:
        raise ValidationError("AWS region is required")
    """
    exit_code = 20
    message = "Validation Error"

class AuthenticationError(ExecutionError):
    """
    Raised when AWS credentials are rejected by the S3 API.

    Use this when boto3 raises a ClientError with error code
    'InvalidClientTokenId', 'AuthFailure', or 'SignatureDoesNotMatch'.

    Example:
        raise AuthenticationError("invalid AWS credentials")
    """
    exit_code = 1
    message = "Authentication Error"

class BucketNotFoundError(ExecutionError):
    """
    Raised when the specified S3 bucket does not exist or is not accessible.

    Use this when boto3 raises a ClientError with error code 'NoSuchBucket'.

    Example:
        raise BucketNotFoundError("Bucket 'my-demo-bucket' not found or not accessible")
    """
    exit_code = 1
    message = "Bucket Not Found"

class LocalFileNotFoundError(ExecutionError):
    """
    Raised when the local file path provided for an Upload File operation
    does not exist on the agent filesystem.

    Use this after os.path.isfile() returns False, before making any S3 API call.

    Example:
        raise LocalFileNotFoundError("Local file not found: '/tmp/reports/q3.csv'")
    """
    exit_code = 1
    message = "Local File Not Found"

class PermissionDeniedError(ExecutionError):
    """
    Raised when the AWS IAM credentials lack the required S3 permissions.

    Use this when boto3 raises a ClientError with error code 'AccessDenied'.

    Example:
        raise PermissionDeniedError("Permission denied for operation on 'my-demo-bucket'")
    """
    exit_code = 1
    message = "Permission Denied"

class NetworkError(ExecutionError):
    """
    Raised when a network-level failure prevents communication with the S3 endpoint.

    Use this when boto3/botocore raises EndpointConnectionError,
    ConnectTimeoutError, or any other connection-related exception.

    Example:
        raise NetworkError("Cannot connect to S3 endpoint after 3 retries")
    """
    exit_code = 1
    message = "Network Error"

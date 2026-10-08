"""
Utility functions for the AWS Object Storage extension.

Provides:
- create_s3_client: S3 client factory — constructs boto3 S3 client from credentials
- get_max_records: Reads UE_MAX_OUTPUT_RECORDS environment variable with safe default
- format_objects_table: Caps object list and renders ASCII table for STDOUT
- classify_boto3_error: Translates boto3/botocore exceptions to extension exceptions
"""
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

import boto3
import botocore.exceptions
from tabulate import tabulate

from exceptions import (
    S3AuthenticationError,
    S3BucketNotFoundError,
    S3InvalidRegionError,
    S3OperationError,
    S3UploadError,
)

logger = logging.getLogger("UNV")

_DEFAULT_MAX_RECORDS: int = 100

_AUTH_ERROR_CODES: frozenset[str] = frozenset({
    "InvalidClientTokenId",
    "AuthFailure",
    "SignatureDoesNotMatch",
    "InvalidAccessKeyId",
})
_BUCKET_NOT_FOUND_CODES: frozenset[str] = frozenset({"NoSuchBucket"})
_REGION_ERROR_CODES: frozenset[str] = frozenset({"InvalidRegion"})


def create_s3_client(
    aws_access_key_id: str,
    aws_secret_access_key: str,
    region_name: str,
) -> Any:
    """
    Create and return a configured boto3 S3 client.

    Args:
        aws_access_key_id: AWS Access Key ID (from UAC Credential user field).
        aws_secret_access_key: AWS Secret Access Key (from UAC Credential password field).
        region_name: AWS region identifier (e.g., 'us-east-1').

    Returns:
        A boto3 S3 client instance.

    Raises:
        S3InvalidRegionError: If region_name is empty or blank.
    """
    if not region_name.strip():
        raise S3InvalidRegionError("Region name must not be empty.")
    logger.info("Creating S3 client for region: %s", region_name)
    client: Any = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name,
    )
    logger.debug("S3 client created successfully for region: %s", region_name)
    return client


def get_max_records() -> int:
    """
    Read and return the UE_MAX_OUTPUT_RECORDS environment variable.

    Returns:
        Parsed positive integer value. Falls back to 100 if the variable is
        absent, non-integer, or less than 1.
    """
    raw: str = os.environ.get("UE_MAX_OUTPUT_RECORDS", "")
    try:
        value: int = int(raw)
        if value < 1:
            raise ValueError("Value must be a positive integer.")
        logger.info("UE_MAX_OUTPUT_RECORDS effective cap: %d", value)
        return value
    except (ValueError, TypeError):
        logger.info(
            "UE_MAX_OUTPUT_RECORDS not set or invalid (%r); defaulting to %d",
            raw,
            _DEFAULT_MAX_RECORDS,
        )
        return _DEFAULT_MAX_RECORDS


def format_objects_table(
    objects: list[dict],
    max_records: Optional[int] = None,
) -> tuple[str, list[dict], int, Optional[str]]:
    """
    Apply the output cap to an S3 object list and render an ASCII table.

    Each object dict must contain:
        - 'key' (str): S3 object key.
        - 'size' (int): Object size in bytes.
        - 'last_modified' (datetime | str): Last modified timestamp.

    Args:
        objects: Full list of S3 object records.
        max_records: Maximum rows to display. Reads UE_MAX_OUTPUT_RECORDS if None.

    Returns:
        A 4-tuple of:
            - table_str: Rendered ASCII table string (rounded_outline format).
            - sliced_objects: Records capped to max_records.
            - total_count: Total number of objects before capping.
            - truncation_notice: Warning string when displayed < total, else None.
    """
    if max_records is None:
        max_records = get_max_records()

    total_count: int = len(objects)
    sliced_objects: list[dict] = objects[:max_records]
    displayed_count: int = len(sliced_objects)

    rows: list[list] = []
    for obj in sliced_objects:
        last_modified: Any = obj["last_modified"]
        if isinstance(last_modified, datetime):
            last_modified_str: str = (
                last_modified.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            )
        else:
            last_modified_str = str(last_modified)
        rows.append([obj["key"], obj["size"], last_modified_str])

    table_str: str = tabulate(
        rows,
        headers=["Key", "Size (B)", "Last Modified"],
        tablefmt="rounded_outline",
    )

    truncation_notice: Optional[str] = None
    if displayed_count < total_count:
        truncation_notice = (
            f"Note: Displaying {displayed_count} of {total_count} objects. "
            "Set UE_MAX_OUTPUT_RECORDS to increase."
        )
        logger.warning(
            "Output truncated: displaying %d of %d objects",
            displayed_count,
            total_count,
        )

    return table_str, sliced_objects, total_count, truncation_notice


def classify_boto3_error(exc: Exception, is_upload: bool = False) -> None:
    """
    Classify a boto3 or botocore exception and raise the matching extension exception.

    Error code mapping:
        InvalidClientTokenId | AuthFailure | SignatureDoesNotMatch | InvalidAccessKeyId
            → S3AuthenticationError
        NoSuchBucket
            → S3BucketNotFoundError
        AccessDenied (bucket scope)
            → S3BucketNotFoundError
        InvalidRegion
            → S3InvalidRegionError
        Unclassified ClientError when is_upload=True
            → S3UploadError
        All remaining ClientError / BotoCoreError
            → S3OperationError

    Args:
        exc: The caught exception instance.
        is_upload: True when called from within an upload_file operation.

    Raises:
        S3AuthenticationError, S3BucketNotFoundError, S3InvalidRegionError,
        S3UploadError, or S3OperationError — always raises, never returns normally.
    """
    if isinstance(exc, botocore.exceptions.ClientError):
        error_response: dict = exc.response.get("Error", {})
        error_code: str = error_response.get("Code", "")
        error_message: str = error_response.get("Message", str(exc))
        detail: str = f"{error_code} — {error_message}"

        logger.error("AWS ClientError: code=%s, message=%s", error_code, error_message)

        if error_code in _AUTH_ERROR_CODES:
            raise S3AuthenticationError(detail)
        if error_code in _BUCKET_NOT_FOUND_CODES:
            raise S3BucketNotFoundError(detail)
        if error_code == "AccessDenied":
            raise S3BucketNotFoundError(detail)
        if error_code in _REGION_ERROR_CODES:
            raise S3InvalidRegionError(detail)
        if is_upload:
            raise S3UploadError(detail)
        raise S3OperationError(detail)

    if isinstance(exc, botocore.exceptions.BotoCoreError):
        logger.error("AWS BotoCoreError: %s", str(exc))
        raise S3OperationError(str(exc))

    logger.error("Unexpected error during S3 operation: %s", str(exc))
    raise S3OperationError(str(exc))

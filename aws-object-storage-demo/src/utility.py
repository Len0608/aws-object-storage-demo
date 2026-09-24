"""
Utility module for AWS Object Storage Demo Universal Extension.

Provides:
- S3ClientManager: boto3 S3 client creation and S3 operations (list, upload)
- OutputFormatter: ASCII table formatting and truncation note generation
"""

import logging
import os
from typing import Any

import boto3
from botocore.exceptions import ClientError
from tabulate import tabulate

from exceptions import (
    AuthenticationError,
    BucketNotFoundError,
    NetworkError,
    PermissionDeniedError,
)

logger = logging.getLogger("UNV")

# Boto3 ClientError codes that map to specific extension exceptions
_AUTH_ERROR_CODES = {"InvalidClientTokenId", "AuthFailure", "SignatureDoesNotMatch"}
_BUCKET_NOT_FOUND_CODES = {"NoSuchBucket"}
_PERMISSION_ERROR_CODES = {"AccessDenied"}
_NETWORK_ERROR_CODES = {"EndpointConnectionError", "ConnectTimeoutError"}


def _classify_client_error(error: ClientError) -> Exception:
    """
    Map a boto3 ClientError to the appropriate extension exception.

    Args:
        error: The ClientError raised by boto3.

    Returns:
        An instance of the appropriate extension exception.
    """
    error_code = error.response.get("Error", {}).get("Code", "")
    logger.debug("boto3 ClientError code: %s", error_code)

    if error_code in _AUTH_ERROR_CODES:
        return AuthenticationError("invalid AWS credentials")
    if error_code in _BUCKET_NOT_FOUND_CODES:
        bucket = error.response.get("Error", {}).get("BucketName", "<unknown>")
        return BucketNotFoundError("Bucket '%s' not found or not accessible" % bucket)
    if error_code in _PERMISSION_ERROR_CODES:
        return PermissionDeniedError("Permission denied for S3 operation")
    if error_code in _NETWORK_ERROR_CODES:
        return NetworkError("Cannot connect to S3 endpoint")
    # Re-raise as NetworkError for any unrecognised connection-class errors;
    # callers are responsible for catching unknown ClientError variants.
    return NetworkError("Unexpected S3 error: %s" % str(error))


class S3ClientManager:
    """
    Encapsulates boto3 S3 client creation and the two S3 operations:
    paginated object listing and single-file upload.

    Methods raise extension-specific exceptions for all known boto3 error
    codes; unknown ClientErrors are re-raised as NetworkError so callers
    always receive a typed exception.
    """

    @staticmethod
    def create_client(
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region_name: str,
    ) -> Any:
        """
        Create and return a configured boto3 S3 client.

        Args:
            aws_access_key_id: AWS Access Key ID.
            aws_secret_access_key: AWS Secret Access Key.
            region_name: AWS region identifier (e.g., 'us-east-1').

        Returns:
            A boto3 S3 client object.
        """
        logger.info("Creating boto3 S3 client for region: %s", region_name)
        logger.debug(
            "Client parameters: region=%s, access_key_id=%s",
            region_name,
            "***" if aws_access_key_id else None,
        )
        client = boto3.client(
            "s3",
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        logger.info("S3 client created successfully")
        return client

    @staticmethod
    def list_objects(
        s3_client: Any,
        bucket_name: str,
        max_records: int,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        Paginate through all objects in a bucket and return a display list
        capped at max_records together with the total object count.

        Args:
            s3_client: A boto3 S3 client returned by create_client().
            bucket_name: Name of the S3 bucket to list.
            max_records: Maximum number of objects to include in the display list.

        Returns:
            A tuple of (display_list, total_count) where display_list contains
            dicts with keys 'key', 'size', 'last_modified' (ISO 8601 string),
            and total_count is the count of ALL objects across all pages.

        Raises:
            AuthenticationError: When credentials are rejected by S3.
            BucketNotFoundError: When the specified bucket does not exist.
            PermissionDeniedError: When the caller lacks s3:ListBucket permission.
            NetworkError: For connectivity failures or unclassified ClientErrors.
        """
        logger.info("Listing objects in bucket: %s (max_records=%d)", bucket_name, max_records)

        display_list: list[dict[str, Any]] = []
        total_count: int = 0

        try:
            paginator = s3_client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(Bucket=bucket_name)

            for page_num, page in enumerate(page_iterator, start=1):
                objects = page.get("Contents", [])
                logger.debug("Page %d: %d objects", page_num, len(objects))

                for obj in objects:
                    total_count += 1
                    if len(display_list) < max_records:
                        display_list.append(
                            {
                                "key": obj["Key"],
                                "size": obj["Size"],
                                "last_modified": obj["LastModified"].strftime(
                                    "%Y-%m-%dT%H:%M:%SZ"
                                ),
                            }
                        )

        except ClientError as exc:
            logger.error("boto3 ClientError during list_objects_v2: %s", str(exc))
            raise _classify_client_error(exc) from exc

        logger.info(
            "Object listing complete: %d total objects, %d in display list",
            total_count,
            len(display_list),
        )
        return display_list, total_count

    @staticmethod
    def upload_file(
        s3_client: Any,
        local_file: str,
        bucket_name: str,
        s3_object_key: str,
    ) -> None:
        """
        Upload a local file to the specified S3 bucket and key.

        Args:
            s3_client: A boto3 S3 client returned by create_client().
            local_file: Absolute path to the local file on the agent host.
            bucket_name: Destination S3 bucket name.
            s3_object_key: Destination object key within the bucket.

        Raises:
            AuthenticationError: When credentials are rejected by S3.
            BucketNotFoundError: When the specified bucket does not exist.
            PermissionDeniedError: When the caller lacks s3:PutObject permission.
            NetworkError: For connectivity failures or unclassified ClientErrors.
        """
        logger.info(
            "Uploading file: %s -> s3://%s/%s", local_file, bucket_name, s3_object_key
        )
        logger.debug(
            "Upload parameters: local_file=%s, bucket=%s, key=%s",
            local_file,
            bucket_name,
            s3_object_key,
        )

        try:
            s3_client.upload_file(local_file, bucket_name, s3_object_key)
        except ClientError as exc:
            logger.error("boto3 ClientError during upload_file: %s", str(exc))
            raise _classify_client_error(exc) from exc

        logger.info("File uploaded successfully to s3://%s/%s", bucket_name, s3_object_key)


class OutputFormatter:
    """
    Formats List Objects result data as human-readable output for STDOUT.

    Methods are static; no instance state is maintained.
    """

    @staticmethod
    def format_table(objects: list[dict[str, Any]]) -> str:
        """
        Produce a rounded_outline ASCII table from a list of S3 object dicts.

        Args:
            objects: List of dicts, each with keys 'key', 'size', 'last_modified'.

        Returns:
            Formatted table string suitable for printing to STDOUT.
        """
        logger.debug("Formatting table for %d objects", len(objects))
        rows = [[obj["key"], obj["size"], obj["last_modified"]] for obj in objects]
        table = tabulate(
            rows,
            headers=["Key", "Size", "Last Modified"],
            tablefmt="rounded_outline",
        )
        logger.debug("Table formatting complete")
        return table

    @staticmethod
    def format_truncation_note(max_records: int, total_count: int) -> str:
        """
        Build the truncation note line shown below the table when results are capped.

        Args:
            max_records: The record cap that was applied.
            total_count: Total number of objects found in the bucket.

        Returns:
            Truncation note string.
        """
        return (
            "Note: Output limited to %d records. "
            "Total objects in bucket: %d." % (max_records, total_count)
        )

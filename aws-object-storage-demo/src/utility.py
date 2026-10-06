"""
Utility module for the AWS Object Storage Demo UAC Universal Extension.

Provides S3ClientUtility — a class that encapsulates all AWS S3 API interactions
including client initialization, object listing via paginator, file upload, ETag
retrieval, and boto3 exception classification into typed extension exceptions.
"""
import logging
from typing import Any, NoReturn

import boto3
import boto3.exceptions
import botocore.exceptions

from exceptions import (
    S3AccessDeniedError,
    S3AuthenticationError,
    S3BucketNotFoundError,
    S3ConnectionError,
    S3UploadError,
)

logger = logging.getLogger("UNV")

_AUTH_ERROR_CODES: frozenset[str] = frozenset({
    "InvalidClientTokenId",
    "AuthFailure",
    "SignatureDoesNotMatch",
    "InvalidAccessKeyId",
})


class S3ClientUtility:
    """
    Encapsulates all AWS S3 API interactions for the AWS Object Storage Demo extension.

    Handles client initialization, object listing via paginator, file upload,
    ETag retrieval, and boto3 exception classification into typed extension exceptions.
    """

    def __init__(self, access_key_id: str, secret_access_key: str, region_name: str) -> None:
        """
        Initialize the S3 client with static AWS credentials and a target region.

        Args:
            access_key_id: AWS Access Key ID (from UAC Credential user attribute).
            secret_access_key: AWS Secret Access Key (from UAC Credential password attribute).
            region_name: AWS region where the target bucket resides (e.g. 'us-east-1').
        """
        logger.info("Initializing S3 client for region: %s", region_name)
        self._client = boto3.client(
            "s3",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region_name,
        )
        logger.debug("S3 client initialized")

    def list_objects(self, bucket_name: str) -> tuple[list[dict[str, Any]], int]:
        """
        List all objects in a bucket using the list_objects_v2 paginator.

        Paginates through all result pages and collects every object's Key, Size,
        and LastModified into a flat list. The caller is responsible for applying
        any output cap and formatting timestamps.

        Args:
            bucket_name: Name of the S3 bucket to list.

        Returns:
            A tuple (objects, total_count) where objects is a list of dicts with
            keys 'Key' (str), 'Size' (int), 'LastModified' (datetime UTC), and
            total_count is the number of objects collected across all pages.

        Raises:
            S3AuthenticationError: When AWS credentials are rejected.
            S3BucketNotFoundError: When the bucket does not exist or is in a different region.
            S3AccessDeniedError: When the IAM policy denies the ListBucket operation.
            S3ConnectionError: When a network-level failure prevents reaching AWS endpoints.
        """
        logger.info("Listing all objects in bucket: %s", bucket_name)
        objects: list[dict[str, Any]] = []

        try:
            paginator = self._client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=bucket_name):
                page_contents = page.get("Contents", [])
                logger.debug("Received page with %d object(s)", len(page_contents))
                for obj in page_contents:
                    objects.append({
                        "Key": obj["Key"],
                        "Size": obj["Size"],
                        "LastModified": obj["LastModified"],
                    })
        except botocore.exceptions.ClientError as e:
            self._classify_client_error(e, context="list_objects")
        except botocore.exceptions.ConnectionError as e:
            logger.error("Network error listing objects in '%s': %s", bucket_name, str(e))
            raise S3ConnectionError(str(e))

        total_count = len(objects)
        logger.info("Collected %d object(s) from bucket '%s'", total_count, bucket_name)
        return objects, total_count

    def upload_file(self, local_file_path: str, bucket_name: str, s3_object_key: str) -> None:
        """
        Upload a local file to the specified S3 bucket and key.

        Args:
            local_file_path: Absolute path to the local file on the agent host.
            bucket_name: Name of the S3 bucket destination.
            s3_object_key: Target object key within the bucket.

        Raises:
            S3AuthenticationError: When AWS credentials are rejected.
            S3BucketNotFoundError: When the bucket does not exist.
            S3AccessDeniedError: When the IAM policy denies the PutObject operation.
            S3ConnectionError: When a network-level failure prevents reaching AWS endpoints.
            S3UploadError: When the upload fails or is interrupted mid-transfer.
        """
        logger.info(
            "Uploading '%s' to s3://%s/%s",
            local_file_path, bucket_name, s3_object_key,
        )
        try:
            self._client.upload_file(local_file_path, bucket_name, s3_object_key)
            logger.info("Upload complete: s3://%s/%s", bucket_name, s3_object_key)
        except boto3.exceptions.S3UploadFailedError as e:
            logger.error("Upload failed for '%s': %s", local_file_path, str(e))
            raise S3UploadError(str(e))
        except botocore.exceptions.ClientError as e:
            self._classify_client_error(e, context="upload_file")
        except botocore.exceptions.ConnectionError as e:
            logger.error("Network error uploading '%s': %s", local_file_path, str(e))
            raise S3ConnectionError(str(e))

    def get_etag(self, bucket_name: str, s3_object_key: str) -> str:
        """
        Retrieve the ETag of an S3 object via head_object, with surrounding quotes stripped.

        S3 returns ETags wrapped in double-quotes (e.g. '"abc123"'); this method
        strips those characters before returning.

        Args:
            bucket_name: Name of the S3 bucket.
            s3_object_key: Key of the S3 object.

        Returns:
            ETag string with surrounding double-quote characters removed.

        Raises:
            S3AuthenticationError: When AWS credentials are rejected.
            S3AccessDeniedError: When the IAM policy denies the HeadObject operation.
            S3ConnectionError: When a network-level failure prevents reaching AWS endpoints.
        """
        logger.info("Retrieving ETag for s3://%s/%s", bucket_name, s3_object_key)
        try:
            response = self._client.head_object(Bucket=bucket_name, Key=s3_object_key)
            etag: str = response["ETag"].strip('"')
            logger.debug("ETag retrieved: %s", etag)
            return etag
        except botocore.exceptions.ClientError as e:
            self._classify_client_error(e, context="get_etag")
        except botocore.exceptions.ConnectionError as e:
            logger.error(
                "Network error retrieving ETag for s3://%s/%s: %s",
                bucket_name, s3_object_key, str(e),
            )
            raise S3ConnectionError(str(e))

    def _classify_client_error(
        self,
        error: botocore.exceptions.ClientError,
        context: str,
    ) -> NoReturn:
        """
        Classify a botocore ClientError by error code and raise the matching typed exception.

        Args:
            error: The ClientError instance to classify.
            context: Short label identifying the calling operation, used in log messages.

        Raises:
            S3AuthenticationError: For authentication-related error codes.
            S3BucketNotFoundError: When the error code is NoSuchBucket.
            S3AccessDeniedError: When the error code is AccessDenied.
            S3UploadError: For any other ClientError code.
        """
        error_code: str = error.response.get("Error", {}).get("Code", "")
        logger.error(
            "S3 ClientError in %s (code=%s): %s",
            context, error_code, str(error),
        )
        if error_code in _AUTH_ERROR_CODES:
            raise S3AuthenticationError(str(error))
        if error_code == "NoSuchBucket":
            raise S3BucketNotFoundError(str(error))
        if error_code == "AccessDenied":
            raise S3AccessDeniedError(str(error))
        raise S3UploadError(str(error))

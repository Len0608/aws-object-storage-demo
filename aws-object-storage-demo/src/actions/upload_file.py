"""Upload File action — uploads a local file to an S3 bucket."""

import logging
import os

import botocore.exceptions

from actions.output import ActionOutput
from exceptions import LocalFileNotFoundError, ValidationError
from fields.input import InputFields
from fields.output import OutputFields
from manager import ExtensionManager
from utility import classify_boto3_error, create_s3_client

logger = logging.getLogger("UNV")
extension_manager = ExtensionManager()


def upload_file(input_data: InputFields) -> ActionOutput:
    """Upload a local file from the agent host to the specified S3 bucket and key.

    Validates that the local file exists before making any AWS API calls.
    Writes confirmation messages to STDOUT on success and populates the
    result_summary OutputField with the S3 destination URI.

    Args:
        input_data: Validated input fields.

    Returns:
        ActionOutput containing bucket, key, and file_size.

    Raises:
        ValidationError: If a required field is missing or empty.
        LocalFileNotFoundError: If the local file does not exist on the agent host.
        S3AuthenticationError: If AWS credentials are rejected.
        S3BucketNotFoundError: If the target bucket does not exist or is inaccessible.
        S3InvalidRegionError: If the region is invalid or endpoint cannot be resolved.
        S3UploadError: If the upload fails or is interrupted mid-transfer.
        S3OperationError: For any other unclassified AWS error.
    """
    logger.info("Starting upload_file action")

    # Step 1: Input validation — fast-fail on missing fields
    if not input_data.aws_credentials:
        raise ValidationError("aws_credentials is required")
    if not input_data.aws_region or not input_data.aws_region.value.strip():
        raise ValidationError("aws_region is required and must not be empty")
    if not input_data.bucket_name or not input_data.bucket_name.value.strip():
        raise ValidationError("bucket_name is required and must not be empty")
    if not input_data.local_file or not input_data.local_file.value.strip():
        raise ValidationError("local_file is required when action is 'Upload File'")
    if not input_data.s3_object_key or not input_data.s3_object_key.value.strip():
        raise ValidationError("s3_object_key is required when action is 'Upload File'")

    aws_region: str = input_data.aws_region.value.strip()
    bucket_name: str = input_data.bucket_name.value.strip()
    local_file: str = input_data.local_file.value.strip()
    s3_object_key: str = input_data.s3_object_key.value.strip()

    logger.debug(
        "Input: local_file=%s, bucket_name=%s, s3_object_key=%s, aws_region=%s",
        local_file,
        bucket_name,
        s3_object_key,
        aws_region,
    )

    # Initialise real-time output field
    output_fields = OutputFields()
    output_fields.update(result_summary="Validating local file...")

    # Step 2: Verify local file exists and obtain size
    logger.info("Verifying local file exists: %s", local_file)
    if not os.path.exists(local_file):
        logger.error("Local file not found: %s", local_file)
        raise LocalFileNotFoundError(f"Local file not found — {local_file}")

    file_size: int = os.path.getsize(local_file)
    logger.debug("Local file found: %s (%d bytes)", local_file, file_size)

    # Step 3: Establish S3 client
    print(f"Connecting to S3 in region '{aws_region}'")
    s3_client = create_s3_client(
        aws_access_key_id=input_data.aws_credentials.user,
        aws_secret_access_key=input_data.aws_credentials.password,
        region_name=aws_region,
    )

    # Step 4: Upload file
    print(f"Uploading '{local_file}' to s3://{bucket_name}/{s3_object_key}")
    logger.info(
        "Uploading '%s' to s3://%s/%s",
        local_file,
        bucket_name,
        s3_object_key,
    )

    output_fields.update(result_summary="Uploading file...")

    try:
        s3_client.upload_file(local_file, bucket_name, s3_object_key)
    except Exception as exc:
        classify_boto3_error(exc, is_upload=True)

    # Step 5: Populate outputs and return
    s3_uri: str = f"s3://{bucket_name}/{s3_object_key}"
    print(f"Uploaded: {s3_uri}")

    result_summary_str: str = f"Uploaded: {s3_uri}"
    output_fields.update(result_summary=result_summary_str)

    logger.info("upload_file action completed: %s (%d bytes)", s3_uri, file_size)
    logger.debug(
        "Returning bucket=%s, key=%s, file_size=%d",
        bucket_name,
        s3_object_key,
        file_size,
    )

    return ActionOutput(
        bucket=bucket_name,
        key=s3_object_key,
        file_size=file_size,
    )

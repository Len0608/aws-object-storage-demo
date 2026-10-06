"""Upload File action — uploads a local file to an S3 bucket."""

import logging
import os

from actions.output import ActionOutput
from exceptions import ValidationError
from fields.input import InputFields
from fields.output import OutputFields
from manager import ExtensionManager
from utility import S3ClientUtility

logger = logging.getLogger("UNV")
extension_manager = ExtensionManager()


def upload_file(input_data: InputFields) -> ActionOutput:
    """Upload a local file from the agent host to the specified S3 bucket and key.

    Validates that the local file exists before making any AWS API calls.
    Writes a confirmation message to STDOUT on success and populates Extension
    Output with the S3 URI, bucket, key, and ETag.

    Args:
        input_data: Validated input fields.

    Returns:
        ActionOutput containing s3_uri, bucket, key, and etag.

    Raises:
        ValidationError: If the local file does not exist on the agent host.
        S3AuthenticationError: If AWS credentials are rejected.
        S3BucketNotFoundError: If the target bucket does not exist.
        S3AccessDeniedError: If the IAM policy denies the PutObject operation.
        S3ConnectionError: If a network-level failure prevents reaching AWS.
        S3UploadError: If the upload fails or is interrupted mid-transfer.
    """
    logger.info("Starting upload_file action")

    local_file: str = input_data.local_file.value
    bucket_name: str = input_data.bucket_name.value
    s3_object_key: str = input_data.s3_object_key.value
    aws_region: str = input_data.aws_region.value

    logger.debug(
        "Input: local_file=%s, bucket_name=%s, s3_object_key=%s, aws_region=%s",
        local_file, bucket_name, s3_object_key, aws_region,
    )

    # Initialise real-time output fields
    output_fields = OutputFields()
    output_fields.update(status="Validating")

    # Step 1: Validate local file
    logger.info("Validating local file: %s", local_file)
    if not os.path.isfile(local_file):
        logger.error("Local file not found: %s", local_file)
        raise ValidationError(f"Local file {local_file} not found")
    logger.debug("Local file exists: %s", local_file)

    # Step 2: Initialize S3 client
    output_fields.update(status="Initializing")
    logger.info("Initializing S3 client for region: %s", aws_region)
    s3_client = S3ClientUtility(
        access_key_id=input_data.aws_credentials.user,
        secret_access_key=input_data.aws_credentials.password,
        region_name=aws_region,
    )

    # Step 3: Upload the file
    output_fields.update(status="Uploading")
    logger.info(
        "Uploading '%s' to s3://%s/%s",
        local_file, bucket_name, s3_object_key,
    )
    s3_client.upload_file(
        local_file_path=local_file,
        bucket_name=bucket_name,
        s3_object_key=s3_object_key,
    )
    logger.info("Upload complete: s3://%s/%s", bucket_name, s3_object_key)

    # Step 4: Retrieve the ETag
    output_fields.update(status="Retrieving ETag")
    logger.info("Retrieving ETag for s3://%s/%s", bucket_name, s3_object_key)
    etag: str = s3_client.get_etag(bucket_name=bucket_name, s3_object_key=s3_object_key)
    logger.debug("ETag: %s", etag)

    # Step 5: Write STDOUT confirmation
    s3_uri: str = f"s3://{bucket_name}/{s3_object_key}"
    print(f"Uploaded {local_file} to {s3_uri}")

    # Step 6: Populate output-only fields
    output_fields.update(
        status="Upload successful",
        result=s3_uri,
    )

    logger.info("upload_file action completed: s3_uri=%s, etag=%s", s3_uri, etag)

    # Step 7: Return ActionOutput
    return ActionOutput(
        s3_uri=s3_uri,
        bucket=bucket_name,
        key=s3_object_key,
        etag=etag,
    )

"""Upload File action — uploads a local file to the specified S3 bucket."""

import logging
import os

from actions.output import ActionOutput
from exceptions import ExecutionError, LocalFileNotFoundError, ValidationError
from fields.input import InputFields
from fields.output import OutputFields
from manager import ExtensionManager
from utility import S3ClientManager

logger = logging.getLogger("UNV")
extension_manager = ExtensionManager()


def upload_file(input_data: InputFields) -> ActionOutput:
    """Upload a local file from the UAC agent host to an S3 bucket.

    Validates that the local file exists before making any S3 API call.
    On success, prints the full S3 URI to STDOUT and sets output fields.

    Args:
        input_data: Validated input fields.

    Returns:
        ActionOutput containing the S3 URI of the uploaded object.
    """
    logger.info("Starting upload_file action")

    # ------------------------------------------------------------------ #
    # Step 1: Input validation                                             #
    # ------------------------------------------------------------------ #
    logger.debug(
        "Input: bucket_name=%s, local_file=%s, s3_object_key=%s",
        input_data.bucket_name.value if input_data.bucket_name else None,
        input_data.local_file.value if input_data.local_file else None,
        input_data.s3_object_key.value if input_data.s3_object_key else None,
    )

    if input_data.aws_credentials is None:
        raise ValidationError("AWS credentials are required")

    if not input_data.aws_region or not input_data.aws_region.value.strip():
        raise ValidationError("AWS region is required")

    if not input_data.bucket_name or not input_data.bucket_name.value.strip():
        raise ValidationError("Bucket name is required")

    if not input_data.local_file or not input_data.local_file.value.strip():
        raise ValidationError("Local file path is required")

    if not input_data.s3_object_key or not input_data.s3_object_key.value.strip():
        raise ValidationError("S3 object key is required")

    aws_region = input_data.aws_region.value.strip()
    bucket_name = input_data.bucket_name.value.strip()
    local_file = input_data.local_file.value.strip()
    s3_object_key = input_data.s3_object_key.value.strip()
    aws_access_key_id: str = input_data.aws_credentials.user
    aws_secret_access_key: str = input_data.aws_credentials.password

    # ------------------------------------------------------------------ #
    # Step 2: Initialise OutputFields for real-time UI updates            #
    # ------------------------------------------------------------------ #
    output_fields = OutputFields()
    output_fields.update(status="Validating local file…")

    # ------------------------------------------------------------------ #
    # Step 3: Validate local file existence                                #
    # ------------------------------------------------------------------ #
    logger.info("Validating local file existence: %s", local_file)
    if not os.path.isfile(local_file):
        logger.error("Local file not found: %s", local_file)
        raise LocalFileNotFoundError("Error: Local file not found: '%s'" % local_file)

    logger.debug("Local file exists: %s", local_file)

    # ------------------------------------------------------------------ #
    # Step 4: Cancellation check                                           #
    # ------------------------------------------------------------------ #
    if extension_manager.is_cancelled():
        logger.warning("Operation cancelled before S3 client creation")
        raise ExecutionError("Operation cancelled by user")

    # ------------------------------------------------------------------ #
    # Step 5: Create S3 client                                             #
    # ------------------------------------------------------------------ #
    logger.info("Creating S3 client for region: %s", aws_region)
    s3_client = S3ClientManager.create_client(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region,
    )

    # ------------------------------------------------------------------ #
    # Step 6: Upload file                                                  #
    # ------------------------------------------------------------------ #
    output_fields.update(status="Uploading file to S3…")
    logger.info(
        "Uploading %s to s3://%s/%s", local_file, bucket_name, s3_object_key
    )

    S3ClientManager.upload_file(
        s3_client=s3_client,
        local_file=local_file,
        bucket_name=bucket_name,
        s3_object_key=s3_object_key,
    )

    s3_uri = "s3://%s/%s" % (bucket_name, s3_object_key)
    logger.info("File uploaded successfully: %s", s3_uri)

    # ------------------------------------------------------------------ #
    # Step 7: Print confirmation to STDOUT                                 #
    # ------------------------------------------------------------------ #
    print("Uploaded %s to %s" % (local_file, s3_uri))

    # ------------------------------------------------------------------ #
    # Step 8: Set OutputFields                                             #
    # ------------------------------------------------------------------ #
    status_msg = "Success: Uploaded to %s" % s3_uri
    output_fields.update(
        status=status_msg,
        result=s3_uri,
    )
    logger.debug("OutputFields updated: status=%s, result=%s", status_msg, s3_uri)

    # ------------------------------------------------------------------ #
    # Step 9: Return ActionOutput                                          #
    # ------------------------------------------------------------------ #
    logger.info("upload_file action completed successfully")

    return ActionOutput(s3_uri=s3_uri)

"""List Objects action — lists all objects in an S3 bucket as an ASCII table."""

import logging

import botocore.exceptions

from actions.output import ActionOutput
from exceptions import ValidationError
from fields.input import InputFields
from fields.output import OutputFields
from manager import ExtensionManager
from utility import classify_boto3_error, create_s3_client, format_objects_table

logger = logging.getLogger("UNV")
extension_manager = ExtensionManager()


def list_objects(input_data: InputFields) -> ActionOutput:
    """List all objects in the S3 bucket and display them as an ASCII table.

    Reads UE_MAX_OUTPUT_RECORDS (default 100) to cap displayed output. When
    the total object count exceeds the cap a truncation notice is written to
    both STDOUT and STDERR. The result_summary OutputField is populated with
    the total object count on success.

    Args:
        input_data: Validated input fields.

    Returns:
        ActionOutput containing bucket, object_count, displayed_count, and objects.

    Raises:
        ValidationError: If a required field is missing or empty.
        S3AuthenticationError: If AWS credentials are rejected.
        S3BucketNotFoundError: If the target bucket does not exist or is inaccessible.
        S3InvalidRegionError: If the region is invalid or endpoint cannot be resolved.
        S3OperationError: For any other unclassified AWS error.
    """
    logger.info("Starting list_objects action")

    # Step 1: Input validation — fast-fail on missing fields
    if not input_data.aws_credentials:
        raise ValidationError("aws_credentials is required")
    if not input_data.aws_region or not input_data.aws_region.value.strip():
        raise ValidationError("aws_region is required and must not be empty")
    if not input_data.bucket_name or not input_data.bucket_name.value.strip():
        raise ValidationError("bucket_name is required and must not be empty")

    aws_region: str = input_data.aws_region.value.strip()
    bucket_name: str = input_data.bucket_name.value.strip()

    logger.debug(
        "Input: bucket_name=%s, aws_region=%s",
        bucket_name,
        aws_region,
    )

    # Initialise real-time output field
    output_fields = OutputFields()
    output_fields.update(result_summary="Listing objects...")

    # Step 3: Establish S3 client
    print(f"Connecting to S3 in region '{aws_region}'")
    s3_client = create_s3_client(
        aws_access_key_id=input_data.aws_credentials.user,
        aws_secret_access_key=input_data.aws_credentials.password,
        region_name=aws_region,
    )

    # Step 4: Retrieve all objects via paginated list_objects_v2
    print(f"Listing objects in bucket '{bucket_name}'")
    logger.info("Listing objects in bucket: %s", bucket_name)

    all_objects: list = []
    kwargs: dict = {"Bucket": bucket_name}

    try:
        while True:
            response: dict = s3_client.list_objects_v2(**kwargs)
            for obj in response.get("Contents", []):
                all_objects.append({
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"],
                })
            if not response.get("IsTruncated", False):
                break
            kwargs["ContinuationToken"] = response["NextContinuationToken"]
    except Exception as exc:
        classify_boto3_error(exc)

    logger.info(
        "Collected %d object(s) from bucket '%s'",
        len(all_objects),
        bucket_name,
    )

    # Steps 5–6: Apply output cap and render ASCII table
    table_str, sliced_objects, total_count, truncation_notice = format_objects_table(all_objects)
    displayed_count: int = len(sliced_objects)

    print(table_str)
    if truncation_notice:
        print(truncation_notice)

    # Step 7: Populate result_summary output field and return
    result_summary_str: str = f"{total_count} objects found in bucket"
    output_fields.update(result_summary=result_summary_str)

    logger.info(
        "list_objects action completed: %d object(s) found in '%s'",
        total_count,
        bucket_name,
    )
    logger.debug(
        "Returning bucket=%s, object_count=%d, displayed_count=%d",
        bucket_name,
        total_count,
        displayed_count,
    )

    return ActionOutput(
        bucket=bucket_name,
        object_count=total_count,
        displayed_count=displayed_count,
        objects=sliced_objects,
    )

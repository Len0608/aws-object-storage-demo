"""List Objects action — lists S3 objects in the specified bucket."""

import logging
import os

from actions.output import ActionOutput
from exceptions import ValidationError
from fields.input import InputFields
from fields.output import OutputFields
from manager import ExtensionManager
from utility import OutputFormatter, S3ClientManager

logger = logging.getLogger("UNV")
extension_manager = ExtensionManager()


def list_objects(input_data: InputFields) -> ActionOutput:
    """List objects stored in the specified S3 bucket.

    Retrieves Key, Size (bytes), and Last Modified (ISO 8601) for every
    object, capped at UE_MAX_OUTPUT_RECORDS (default 100).  Results are
    printed as a rounded_outline ASCII table to STDOUT.  If the bucket
    contains more objects than the cap the output is marked as truncated
    with the total object count reported.

    Args:
        input_data: Validated input fields.

    Returns:
        ActionOutput containing the display list, truncation flag, and
        total object count.
    """
    logger.info("Starting list_objects action")

    # ------------------------------------------------------------------ #
    # Step 1: Input validation                                             #
    # ------------------------------------------------------------------ #
    logger.debug(
        "Input: bucket_name=%s, aws_region=%s",
        input_data.bucket_name.value if input_data.bucket_name else None,
        input_data.aws_region.value if input_data.aws_region else None,
    )

    if input_data.aws_credentials is None:
        raise ValidationError("AWS credentials are required")

    if not input_data.aws_region or not input_data.aws_region.value.strip():
        raise ValidationError("AWS region is required")

    if not input_data.bucket_name or not input_data.bucket_name.value.strip():
        raise ValidationError("Bucket name is required")

    aws_region = input_data.aws_region.value.strip()
    bucket_name = input_data.bucket_name.value.strip()
    aws_access_key_id: str = input_data.aws_credentials["user"]
    aws_secret_access_key: str = input_data.aws_credentials["password"]

    # ------------------------------------------------------------------ #
    # Step 2: Read cap configuration                                       #
    # ------------------------------------------------------------------ #
    raw_max = os.environ.get("UE_MAX_OUTPUT_RECORDS", "")
    try:
        max_records = int(raw_max)
    except (ValueError, TypeError):
        max_records = 100
    logger.debug("max_records=%d", max_records)

    # ------------------------------------------------------------------ #
    # Step 3: Initialise OutputFields for real-time UI updates            #
    # ------------------------------------------------------------------ #
    output_fields = OutputFields()
    output_fields.update(status="Listing objects…")

    # ------------------------------------------------------------------ #
    # Step 4: Cancellation check                                           #
    # ------------------------------------------------------------------ #
    if extension_manager.is_cancelled():
        logger.warning("Operation cancelled before S3 client creation")
        from exceptions import ExecutionError
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
    # Step 6: Paginate and collect objects                                 #
    # ------------------------------------------------------------------ #
    output_fields.update(status="Fetching objects from S3…")
    logger.info("Listing objects in bucket: %s", bucket_name)

    display_list, total_count = S3ClientManager.list_objects(
        s3_client=s3_client,
        bucket_name=bucket_name,
        max_records=max_records,
    )

    truncated: bool = total_count > max_records
    logger.info(
        "Listing complete: total_count=%d, display_list=%d, truncated=%s",
        total_count,
        len(display_list),
        truncated,
    )

    # ------------------------------------------------------------------ #
    # Step 7: Format and print STDOUT table                                #
    # ------------------------------------------------------------------ #
    table_str = OutputFormatter.format_table(display_list)
    print(table_str)

    if truncated:
        truncation_note = OutputFormatter.format_truncation_note(max_records, total_count)
        print(truncation_note)
        logger.debug("Truncation note printed: %s", truncation_note)

    # ------------------------------------------------------------------ #
    # Step 8: Set OutputFields                                             #
    # ------------------------------------------------------------------ #
    status_msg = "Success: Listed %d objects in '%s'" % (len(display_list), bucket_name)
    result_msg = "%d objects" % len(display_list)

    output_fields.update(
        status=status_msg,
        result=result_msg,
    )
    logger.debug("OutputFields updated: status=%s, result=%s", status_msg, result_msg)

    # ------------------------------------------------------------------ #
    # Step 9: Return ActionOutput                                          #
    # ------------------------------------------------------------------ #
    logger.info("list_objects action completed successfully")

    return ActionOutput(
        objects=display_list,
        truncated=truncated,
        total_returned=total_count,
    )

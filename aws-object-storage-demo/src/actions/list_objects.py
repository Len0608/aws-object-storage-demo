"""List Objects action — lists all objects in an S3 bucket as an ASCII table."""

import logging
import os
import sys

from tabulate import tabulate

from actions.output import ActionOutput
from fields.input import InputFields
from fields.output import OutputFields
from manager import ExtensionManager
from utility import S3ClientUtility

logger = logging.getLogger("UNV")
extension_manager = ExtensionManager()


def list_objects(input_data: InputFields) -> ActionOutput:
    """List all objects in the S3 bucket and display them as an ASCII table.

    Reads the UE_MAX_OUTPUT_RECORDS environment variable (default 100) to cap
    output. When the total object count exceeds the cap, a truncation notice is
    written to both STDOUT and STDERR and the Extension Output metadata includes
    truncated=True and total_count.

    Args:
        input_data: Validated input fields.

    Returns:
        ActionOutput containing object_count, objects list, and — when
        truncated — truncated flag and total_count.
    """
    logger.info("Starting list_objects action")

    # Step 1: Read configuration
    max_records_raw: str = os.environ.get("UE_MAX_OUTPUT_RECORDS", "100")
    try:
        max_records = int(max_records_raw)
        if max_records <= 0:
            raise ValueError("must be a positive integer")
    except (ValueError, TypeError):
        logger.warning(
            "Invalid UE_MAX_OUTPUT_RECORDS value '%s'; defaulting to 100",
            max_records_raw,
        )
        max_records = 100
    logger.debug("max_records=%d", max_records)

    # Initialise real-time output fields
    output_fields = OutputFields()
    output_fields.update(status="Initializing")

    bucket_name: str = input_data.bucket_name.value
    aws_region: str = input_data.aws_region.value

    logger.debug(
        "Input: bucket_name=%s, aws_region=%s",
        bucket_name, aws_region,
    )

    # Step 2: Initialize S3 client
    logger.info("Initializing S3 client for region: %s", aws_region)
    s3_client = S3ClientUtility(
        access_key_id=input_data.aws_credentials.user,
        secret_access_key=input_data.aws_credentials.password,
        region_name=aws_region,
    )

    # Step 3: Paginate and collect all objects
    output_fields.update(status="Listing objects")
    logger.info("Listing objects in bucket: %s", bucket_name)
    objects, total_count = s3_client.list_objects(bucket_name)
    logger.info("Collected %d object(s) from bucket '%s'", total_count, bucket_name)

    # Step 4: Apply output cap
    truncated: bool = False
    if total_count > max_records:
        truncated = True
        objects = objects[:max_records]
        warning_msg = (
            f"Output truncated: showing {max_records} of {total_count} "
            f"objects in bucket '{bucket_name}'"
        )
        logger.warning(warning_msg)
        print(warning_msg, file=sys.stderr)

    # Step 5 & 6: Format timestamps and build ASCII table
    table_rows = []
    objects_output = []
    for obj in objects:
        last_modified_iso: str = obj["LastModified"].isoformat()
        table_rows.append([obj["Key"], obj["Size"], last_modified_iso])
        objects_output.append({
            "key": obj["Key"],
            "size_bytes": obj["Size"],
            "last_modified": last_modified_iso,
        })

    headers = ["Key", "Size (bytes)", "Last Modified"]
    table: str = tabulate(table_rows, headers=headers, tablefmt="rounded_outline")
    print(table)
    logger.debug("ASCII table printed to STDOUT")

    if truncated:
        truncation_notice = (
            f"[Truncated] Showing {max_records} of {total_count} objects. "
            "Set UE_MAX_OUTPUT_RECORDS to increase the limit."
        )
        print(truncation_notice)
        logger.debug("Truncation notice printed to STDOUT")

    # Step 7: Populate output-only fields
    displayed_count: int = len(objects_output)
    output_fields.update(
        status=f"Listed {displayed_count} objects",
        result=f"{displayed_count} objects in {bucket_name}",
    )

    logger.info("list_objects action completed: %d object(s) listed", displayed_count)

    # Step 8: Return ActionOutput
    return ActionOutput(
        object_count=displayed_count,
        objects=objects_output,
        truncated=True if truncated else None,
        total_count=total_count if truncated else None,
    )

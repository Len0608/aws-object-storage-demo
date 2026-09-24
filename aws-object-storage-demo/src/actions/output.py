"""ActionOutput dataclass for action return values."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger("UNV")


@dataclass
class ActionOutput:
    """Output from action functions.

    Fields
    ------
    objects         List of S3 object dicts (list_objects action).
                    Each dict has keys: 'key', 'size', 'last_modified'.
    truncated       True when the display list was capped at max_records.
    total_returned  Total number of objects found across all pages.
    s3_uri          Full S3 URI of the uploaded object (upload_file action).
    """

    # list_objects fields
    objects: Optional[List[Dict[str, Any]]] = None
    truncated: Optional[bool] = None
    total_returned: Optional[int] = None

    # upload_file fields
    s3_uri: Optional[str] = None

    # No stdout_options / output_options control fields in this template.
    # print_output() and to_dict() always include all populated fields.

    def print_output(self) -> None:
        """Print action results to STDOUT.

        No output-control fields are present in the template, so all
        populated fields are always printed.
        """
        logger.debug("ActionOutput.print_output called")

        if self.s3_uri is not None:
            # upload_file output — table printing is done inside the action;
            # the confirmation line is also printed inside the action.
            # Nothing additional to print here.
            logger.debug("print_output: upload_file path — s3_uri=%s", self.s3_uri)
            return

        if self.objects is not None:
            # list_objects output — the table and truncation note are printed
            # directly inside the action using OutputFormatter.  This method
            # is a no-op for that action to avoid double-printing.
            logger.debug(
                "print_output: list_objects path — %d objects, truncated=%s",
                len(self.objects),
                self.truncated,
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for Extension Output (unv_output).

        No output-control fields are present in the template; all populated
        fields are always included.

        Returns
        -------
        dict
            Populated fields suitable for inclusion in the Extension Output
            result object.
        """
        logger.debug("ActionOutput.to_dict called")
        output: Dict[str, Any] = {}

        if self.objects is not None:
            output["objects"] = self.objects
        if self.truncated is not None:
            output["truncated"] = self.truncated
        if self.total_returned is not None:
            output["total_returned"] = self.total_returned

        if self.s3_uri is not None:
            output["s3_uri"] = self.s3_uri

        logger.debug("ActionOutput.to_dict result keys: %s", list(output.keys()))
        return output

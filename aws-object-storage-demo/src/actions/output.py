"""ActionOutput dataclass for action return values."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ActionOutput:
    """Output from action functions.

    Fields cover both actions:
    - List Objects: object_count, objects, truncated, total_count
    - Upload File: s3_uri, bucket, key, etag

    No stdout_options / output_options control fields exist in this template,
    so print_output() is a no-op (STDOUT is written directly inside each action)
    and to_dict() includes all non-None fields unconditionally.
    """

    # List Objects output fields
    object_count: Optional[int] = None
    objects: Optional[List[Dict[str, Any]]] = None
    truncated: Optional[bool] = None
    total_count: Optional[int] = None

    # Upload File output fields
    s3_uri: Optional[str] = None
    bucket: Optional[str] = None
    key: Optional[str] = None
    etag: Optional[str] = None

    def print_output(self) -> None:
        """No additional STDOUT output.

        Each action function writes its own output (ASCII table, confirmation
        message, truncation notice) directly to STDOUT during execution.
        This method intentionally does nothing.
        """

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for Extension Output (unv_output).

        No output_options control field exists in this template, so all
        non-None fields are included unconditionally.

        Returns:
            Dict containing all non-None output fields.
        """
        output: Dict[str, Any] = {}

        # List Objects fields
        if self.object_count is not None:
            output["object_count"] = self.object_count
        if self.objects is not None:
            output["objects"] = self.objects
        if self.truncated is not None:
            output["truncated"] = self.truncated
        if self.total_count is not None:
            output["total_count"] = self.total_count

        # Upload File fields
        if self.s3_uri is not None:
            output["s3_uri"] = self.s3_uri
        if self.bucket is not None:
            output["bucket"] = self.bucket
        if self.key is not None:
            output["key"] = self.key
        if self.etag is not None:
            output["etag"] = self.etag

        return output

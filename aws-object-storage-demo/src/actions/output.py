"""ActionOutput dataclass for action return values."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ActionOutput:
    """Output from action functions.

    Fields cover both actions:
    - List Objects: bucket, object_count, displayed_count, objects
    - Upload File:  bucket, key, file_size

    No stdout_options / output_options control fields exist in this template,
    so print_output() is a no-op (STDOUT is written directly inside each action)
    and to_dict() includes all non-None fields unconditionally.
    """

    # Shared field
    bucket: Optional[str] = None

    # List Objects fields
    object_count: Optional[int] = None
    displayed_count: Optional[int] = None
    objects: Optional[List[Dict[str, Any]]] = None

    # Upload File fields
    key: Optional[str] = None
    file_size: Optional[int] = None

    def print_output(self) -> None:
        """No additional STDOUT output.

        Each action writes its own output (ASCII table, confirmation
        message, truncation notice) directly to STDOUT during execution.
        This method intentionally does nothing.
        """

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for Extension Output (unv_output result field).

        No output_options control field exists in this template, so all
        non-None fields are included unconditionally.

        Returns:
            Dict containing all non-None output fields.
        """
        output: Dict[str, Any] = {}

        if self.bucket is not None:
            output["bucket"] = self.bucket

        # List Objects fields
        if self.object_count is not None:
            output["object_count"] = self.object_count
        if self.displayed_count is not None:
            output["displayed_count"] = self.displayed_count
        if self.objects is not None:
            output["objects"] = self.objects

        # Upload File fields
        if self.key is not None:
            output["key"] = self.key
        if self.file_size is not None:
            output["file_size"] = self.file_size

        return output

"""OutputFields dataclass for real-time UI updates."""

from dataclasses import dataclass, asdict
from typing import Optional
from universal_extension import ui
from fields.types import Text


@dataclass
class OutputFields:
    """Real-time output fields for UAC UI updates.

    Fields correspond to Output Only fields in template.json:
    - status  (Text Field 5) — brief result message for every completion
    - result  (Text Field 6) — action-specific result value on success
    """

    status: Optional[Text] = None
    result: Optional[Text] = None

    def update(self, **fields):
        """Update fields and sync with UAC UI in real-time.

        Args:
            **fields: Field names and string values to update.
                      String values are automatically wrapped in Text.
        """
        for field_name, field_value in fields.items():
            if hasattr(self, field_name):
                if isinstance(field_value, str):
                    field_value = Text(field_value)
                setattr(self, field_name, field_value)
        ui.update_output_fields(fields)

    def to_dict(self) -> dict:
        """Return current field values as a plain dictionary.

        Text wrappers are unwrapped to their string values.
        None fields are excluded.
        """
        result = {}
        for k, v in asdict(self).items():
            if v is not None:
                result[k] = v["value"] if isinstance(v, dict) and "value" in v else v
        return result

    def clear(self):
        """Reset all output fields to None."""
        self.status = None
        self.result = None

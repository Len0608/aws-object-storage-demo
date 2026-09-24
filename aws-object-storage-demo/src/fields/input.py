"""InputFields dataclass for input parsing and validation."""

from dataclasses import dataclass
from dataclasses import fields as dataclass_fields
from dataclasses import asdict
from pathlib import Path
from typing import Optional, Union, get_type_hints, get_origin, get_args
from fields.output import OutputFields
from fields.types import (
    Text,
    Integer,
    Float,
    Boolean,
    SingleChoice,
    MultiChoice,
    Credential,
    Script,
    Array,
)
from exceptions import DataValidationError, ValidationError
from manager import ExtensionManager

extension_manager = ExtensionManager()


@dataclass
class InputFields:
    """Input fields from UAC with validation.

    Every field name matches the corresponding ``name`` attribute in template.json.
    All user-defined fields are Optional — UAC enforces required-field checks at
    the Controller level before the extension is invoked.

    Fields
    ------
    action         Choice Field 1  — selects the S3 operation (List Objects / Upload File)
    aws_credentials Credential Field 1 — AWS Access Key ID (user) + Secret Access Key (password)
    aws_region     Text Field 1    — AWS region for the target bucket (e.g. us-east-1)
    bucket_name    Text Field 2    — name of the target S3 bucket
    local_file     Text Field 3    — absolute path to local file (Upload File only)
    s3_object_key  Text Field 4    — target object key in S3 bucket (Upload File only)
    """

    # --- User-defined fields (always Optional) ---
    action: Optional[SingleChoice] = None
    aws_credentials: Optional[Credential] = None
    aws_region: Optional[Text] = None
    bucket_name: Optional[Text] = None
    local_file: Optional[Text] = None
    s3_object_key: Optional[Text] = None

    # --- Framework fields ---
    previous_output: Optional[OutputFields] = None
    _skip_validation: bool = False

    @staticmethod
    def preprocess_fields(fields: dict) -> dict:
        """Preprocess raw UAC fields before constructing InputFields.

        Steps:
        1. Drop flattened credential sub-fields (keys containing a dot).
        2. Separate fields that belong to OutputFields (re-run data).
        3. Wrap remaining values in appropriate typed wrappers based on
           type hints declared on this dataclass.

        Args:
            fields: Raw field dict received from UAC.

        Returns:
            Processed dict ready to be unpacked into InputFields(**processed).
        """
        processed: dict = {}
        previous_output_data: dict = {}

        output_field_names = {f.name for f in dataclass_fields(OutputFields)}
        type_hints = get_type_hints(InputFields)

        # Build a mapping: field_name -> concrete wrapper type (unwrapping Optional)
        field_wrapper_types: dict = {}
        for field_name, field_type in type_hints.items():
            base_type = field_type
            if get_origin(field_type) is Union:
                args = get_args(field_type)
                non_none = [a for a in args if a is not type(None)]
                if non_none:
                    base_type = non_none[0]
            field_wrapper_types[field_name] = base_type

        for key, value in fields.items():
            # Drop flattened credential sub-fields (e.g. "aws_credentials.token")
            if "." in key:
                continue

            # Separate previous-run OutputFields data
            if key in output_field_names:
                previous_output_data[key] = value
                continue

            if value is None:
                processed[key] = value
                continue

            wrapper_type = field_wrapper_types.get(key)

            if wrapper_type == SingleChoice:
                if isinstance(value, list):
                    value = SingleChoice(_values=value)
                else:
                    value = SingleChoice(_values=[value])

            elif wrapper_type == MultiChoice:
                if isinstance(value, list):
                    value = MultiChoice(values=value)
                else:
                    value = MultiChoice(values=[value])

            elif wrapper_type == Script:
                if isinstance(value, str):
                    value = Script(path=Path(value))

            elif wrapper_type == Credential:
                if isinstance(value, dict):
                    value = Credential.from_dict(value)

            elif wrapper_type == Text:
                if isinstance(value, str):
                    value = Text(value=value)

            elif wrapper_type == Integer:
                if isinstance(value, int):
                    value = Integer(value=value)

            elif wrapper_type == Float:
                if isinstance(value, (int, float)):
                    value = Float(value=float(value))

            elif wrapper_type == Boolean:
                if isinstance(value, bool):
                    value = Boolean(value=value)

            elif wrapper_type == Array:
                if isinstance(value, list):
                    value = Array(pairs=value)

            processed[key] = value

        # Reconstruct previous OutputFields if re-run data was present
        if previous_output_data:
            for k, v in previous_output_data.items():
                if isinstance(v, str):
                    previous_output_data[k] = Text(value=v)
            processed["previous_output"] = OutputFields(**previous_output_data)

        return processed

    def to_dict(self) -> dict:
        """Convert InputFields to a plain dictionary.

        Wrapper types are unwrapped to their raw values.
        Internal fields (_skip_validation) and None previous_output are excluded.

        Returns:
            Clean dict suitable for inclusion in unv_output.
        """
        data = asdict(self)
        result: dict = {}

        for key, value in data.items():
            if key == "_skip_validation":
                continue
            if key == "previous_output" and value is None:
                continue

            if isinstance(value, dict):
                if "_values" in value:          # SingleChoice
                    result[key] = value["_values"]
                elif "values" in value and len(value) == 1:  # MultiChoice
                    result[key] = value["values"]
                elif "value" in value and len(value) == 1:   # Text / Integer / Float / Boolean
                    result[key] = value["value"]
                elif "path" in value:           # Script
                    result[key] = str(value["path"])
                elif "pairs" in value:          # Array
                    result[key] = value["pairs"]
                else:
                    result[key] = value         # Credential or unknown dict
            else:
                result[key] = value

        return result

    def __post_init__(self):
        """Run field validation after dataclass initialisation."""
        if self._skip_validation:
            return

        self._validate_action()
        self._validate_aws_region()
        self._validate_bucket_name()
        self._validate_local_file()
        self._validate_s3_object_key()

        if extension_manager.has_errors():
            raise DataValidationError(
                f"Validation failed with {extension_manager.error_count()} error(s)"
            )

    # ------------------------------------------------------------------
    # Validation methods
    # ------------------------------------------------------------------

    def _validate_action(self):
        """Validate that action is one of the defined choices."""
        if self.action is not None:
            valid_actions = ["List Objects", "Upload File"]
            if self.action.value not in valid_actions:
                exc = DataValidationError(
                    f"Invalid action '{self.action.value}'. "
                    f"Valid actions: {', '.join(valid_actions)}"
                )
                extension_manager.add_error(exc, field="action", value=self.action.value)

    def _validate_aws_region(self):
        """Validate that aws_region is not empty."""
        if self.aws_region is not None and not self.aws_region.value.strip():
            exc = ValidationError("AWS region is required")
            extension_manager.add_error(exc, field="aws_region")

    def _validate_bucket_name(self):
        """Validate that bucket_name is not empty."""
        if self.bucket_name is not None and not self.bucket_name.value.strip():
            exc = ValidationError("Bucket name is required")
            extension_manager.add_error(exc, field="bucket_name")

    def _validate_local_file(self):
        """Validate local_file when the Upload File action is selected.

        local_file is only visible (and required) when action == 'Upload File'.
        UAC sends an empty string for hidden fields, so check for both None and ''.
        """
        if self.action and self.action.value == "Upload File":
            if not self.local_file or not self.local_file.value.strip():
                exc = ValidationError("Local file path is required")
                extension_manager.add_error(exc, field="local_file")

    def _validate_s3_object_key(self):
        """Validate s3_object_key when the Upload File action is selected.

        s3_object_key is only visible (and required) when action == 'Upload File'.
        UAC sends an empty string for hidden fields, so check for both None and ''.
        """
        if self.action and self.action.value == "Upload File":
            if not self.s3_object_key or not self.s3_object_key.value.strip():
                exc = ValidationError("S3 object key is required")
                extension_manager.add_error(exc, field="s3_object_key")

"""InputFields dataclass for input parsing and validation."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any, Dict, List, get_type_hints, Union, get_origin, get_args
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
from exceptions import DataValidationError
from manager import ExtensionManager
from dataclasses import fields as dataclass_fields
from dataclasses import asdict

extension_manager = ExtensionManager()


@dataclass
class InputFields:
    """Input fields from UAC with validation.

    Define fields based on your template.json fields using wrapper types.
    All fields should use wrapper types from fields.types for type safety.

    All user-defined fields should be Optional[Type] = None
    - UAC Controller enforces required field validation (template.json)
    - By the time fields reach the extension, they may be None
    - Only validate fields that have values (check for None first)
    """

    # User-defined fields - ALWAYS Optional, even if required in template.json
    action: Optional[SingleChoice] = None
    aws_credentials: Optional[Credential] = None
    aws_region: Optional[Text] = None
    bucket_name: Optional[Text] = None
    local_file: Optional[Text] = None
    s3_object_key: Optional[Text] = None
    result_summary: Optional[Text] = None

    # Previous run output (auto-populated for re-runs)
    previous_output: Optional[OutputFields] = None

    # Skip validation flag (internal use only)
    _skip_validation: bool = False

    @staticmethod
    def preprocess_fields(fields: dict) -> dict:
        """Preprocess raw UAC fields before creating InputFields.

        Converts raw UAC values to wrapper type instances:
        1. Filters out flattened credential fields (containing dots)
        2. Wraps values in appropriate wrapper types based on field type hints
        3. Extracts previous OutputFields if present (from re-runs)
        """

        processed = {}
        previous_output_data = {}

        # Get all OutputFields field names for detection
        output_field_names = {f.name for f in dataclass_fields(OutputFields)}

        # Get type hints to detect wrapper types
        type_hints = get_type_hints(InputFields)

        # Map field names to their wrapper types
        field_wrapper_types = {}
        for field_name, field_type in type_hints.items():
            # Get base type (unwrap Optional)
            base_type = field_type
            if get_origin(field_type) is Union:
                args = get_args(field_type)
                # Filter out NoneType to get the actual type
                non_none_args = [arg for arg in args if arg is not type(None)]
                if non_none_args:
                    base_type = non_none_args[0]

            field_wrapper_types[field_name] = base_type

        for key, value in fields.items():
            # Skip flattened credential fields (e.g., "api_credential.token")
            if "." in key:
                continue

            # Check if this field belongs to OutputFields (previous run data)
            if key in output_field_names:
                previous_output_data[key] = value
                continue

            # Skip None values
            if value is None:
                processed[key] = value
                continue

            # Get the wrapper type for this field
            wrapper_type = field_wrapper_types.get(key)

            # Convert to appropriate wrapper type
            if wrapper_type == SingleChoice:
                # UAC sends as list, SingleChoice expects list
                if isinstance(value, list):
                    value = SingleChoice(_values=value)
                else:
                    value = SingleChoice(_values=[value])

            elif wrapper_type == MultiChoice:
                # UAC sends as list, MultiChoice expects list
                if isinstance(value, list):
                    value = MultiChoice(values=value)
                else:
                    value = MultiChoice(values=[value])

            elif wrapper_type == Script:
                # UAC sends as string path, Script expects Path object
                if isinstance(value, str):
                    value = Script(path=Path(value))

            elif wrapper_type == Credential:
                # UAC sends as dict, Credential expects kwargs
                if isinstance(value, dict):
                    value = Credential.from_dict(value)

            elif wrapper_type == Text:
                # Wrap string in Text
                if isinstance(value, str):
                    value = Text(value=value)

            elif wrapper_type == Integer:
                # Wrap int in Integer
                if isinstance(value, int):
                    value = Integer(value=value)

            elif wrapper_type == Float:
                # Wrap float in Float
                if isinstance(value, (int, float)):
                    value = Float(value=float(value))

            elif wrapper_type == Boolean:
                # Wrap bool in Boolean
                if isinstance(value, bool):
                    value = Boolean(value=value)

            elif wrapper_type == Array:
                # UAC sends as list of dicts, Array expects list of dicts
                if isinstance(value, list):
                    value = Array(pairs=value)

            processed[key] = value

        # If we found previous output fields, create OutputFields instance
        if previous_output_data:
            # Wrap Text fields in previous output
            for key, val in previous_output_data.items():
                if isinstance(val, str):
                    previous_output_data[key] = Text(value=val)
            processed["previous_output"] = OutputFields(**previous_output_data)

        return processed

    def to_dict(self) -> dict:
        """Convert to dict, unwrapping wrapper types and excluding internal fields.

        Returns:
            Dict with unwrapped field values, excluding _skip_validation and None previous_output
        """

        data = asdict(self)

        # Unwrap wrapper types to their raw values
        result = {}
        for key, value in data.items():
            # Skip internal fields
            if key == "_skip_validation":
                continue

            # Skip None previous_output
            if key == "previous_output" and value is None:
                continue

            # Unwrap wrapper types
            if isinstance(value, dict):
                # Check if it's a wrapper type dict representation
                if "_values" in value:  # SingleChoice
                    result[key] = value["_values"]
                elif "values" in value and len(value) == 1:  # MultiChoice
                    result[key] = value["values"]
                elif "value" in value and len(value) == 1:  # Text, Integer, Float, Boolean
                    result[key] = value["value"]
                elif "path" in value:  # Script
                    result[key] = str(value["path"])
                elif "pairs" in value:  # Array
                    result[key] = value["pairs"]
                elif "user" in value:  # Credential
                    result[key] = value
                else:
                    result[key] = value
            else:
                result[key] = value

        return result

    def __post_init__(self):
        """Validate fields after initialization."""
        if self._skip_validation:
            return

        # Call validation methods
        self._validate_action()
        self._validate_aws_credentials()
        self._validate_aws_region()
        self._validate_bucket_name()
        self._validate_local_file()
        self._validate_s3_object_key()

        # Raise once if errors collected
        if extension_manager.has_errors():
            raise DataValidationError(
                f"Validation failed with {extension_manager.error_count()} error(s)"
            )

    def _validate_action(self):
        """Validate action field value is one of the allowed choices."""
        if self.action is not None:
            valid_actions = ["List Objects", "Upload File"]
            if self.action.value not in valid_actions:
                exc = DataValidationError(
                    f"Invalid action '{self.action.value}'. Valid actions: {', '.join(valid_actions)}"
                )
                extension_manager.add_error(exc, field="action", value=self.action.value)

    def _validate_aws_credentials(self):
        """Validate aws_credentials field is present."""
        if self.aws_credentials is not None:
            if not self.aws_credentials.user:
                exc = DataValidationError(
                    "aws_credentials must contain an AWS Access Key ID in the user attribute"
                )
                extension_manager.add_error(exc, field="aws_credentials")
            if not self.aws_credentials.password:
                exc = DataValidationError(
                    "aws_credentials must contain an AWS Secret Access Key in the password attribute"
                )
                extension_manager.add_error(exc, field="aws_credentials")

    def _validate_aws_region(self):
        """Validate aws_region is a non-empty string."""
        if self.aws_region is not None and not self.aws_region.value.strip():
            exc = DataValidationError("aws_region must be a non-empty string (e.g., us-east-1)")
            extension_manager.add_error(exc, field="aws_region")

    def _validate_bucket_name(self):
        """Validate bucket_name is a non-empty string."""
        if self.bucket_name is not None and not self.bucket_name.value.strip():
            exc = DataValidationError("bucket_name must be a non-empty string")
            extension_manager.add_error(exc, field="bucket_name")

    def _validate_local_file(self):
        """Validate local_file when action is Upload File."""
        if self.action and self.action.value == "Upload File":
            if not self.local_file or not self.local_file.value.strip():
                exc = DataValidationError(
                    "local_file is required when action is 'Upload File'"
                )
                extension_manager.add_error(exc, field="local_file")

    def _validate_s3_object_key(self):
        """Validate s3_object_key when action is Upload File."""
        if self.action and self.action.value == "Upload File":
            if not self.s3_object_key or not self.s3_object_key.value.strip():
                exc = DataValidationError(
                    "s3_object_key is required when action is 'Upload File'"
                )
                extension_manager.add_error(exc, field="s3_object_key")

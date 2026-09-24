"""Actions module — business logic implementations."""

from actions.list_objects import list_objects
from actions.output import ActionOutput
from actions.upload_file import upload_file
from manager import ExtensionManager

extension_manager = ExtensionManager()

# Map action choice values to their implementing functions.
# Keys must match the SingleChoice option values defined in template.json.
ACTION_MAPPER = {
    "List Objects": list_objects,
    "Upload File": upload_file,
}

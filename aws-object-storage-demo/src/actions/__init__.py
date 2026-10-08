"""Actions module — business logic implementations."""

from actions.list_objects import list_objects
from actions.output import ActionOutput
from actions.upload_file import upload_file

# Maps input_data.action.value strings to action functions
ACTION_MAPPER = {
    "List Objects": list_objects,
    "Upload File": upload_file,
}

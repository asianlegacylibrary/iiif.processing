# manifest functions
from .get_spaces_directory_files import get_spaces_directory_files, go_through_directory
from .load_templates import load_templates
from .update_document_placeholders import update_json_placeholders, update_canvas_items
from .get_image_index import get_image_index, get_trailing_number, standardize_digits
from .list_directories import list_test_directories, list_client_directories, get_directory_images
from .build_manifest import build_manifest, build_manifest_alt
from .build_manifest_template_structure import build_manifest_template_structure
from .file_processing import create_structure_and_copy, create_web_files, upload_manifest
from .authorize_google import authorize_google

# logging
from .print_logger import Logger, conf_log
from .configure_logger import configure_logger


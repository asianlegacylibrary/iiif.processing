from functions import load_templates, update_json_placeholders
from templates.placeholder_values import manifest_values
from config.config import TEMPLATE_DIR


def build_manifest_template_structure():
    print(f'...build_manifest_template_structure()')
    # load json templates
    manifest_template, canvas_template, seq_template = load_templates(TEMPLATE_DIR)
    # update the manifest placeholders
    manifest_structure = update_json_placeholders(manifest_template, manifest_values)
    print(manifest_structure)
    return manifest_structure, canvas_template, seq_template

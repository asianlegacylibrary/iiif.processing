from functions import list_directory_files, load_templates, update_json_placeholders, build_manifest
from templates.placeholder_values import p as placeholder_values
from config.config import TEMPLATE_DIR


def build_manifest_template_structure():
    print(f"build_manifest_from_template...")
    # load json templates
    manifest_template, canvas_template = load_templates(TEMPLATE_DIR)

    # update the manifest placeholders
    manifest_structure = update_json_placeholders(manifest_template, placeholder_values)
    # print(manifest)

    # build manifest for specific folder
    # page_key = next(iter(page.keys()))
    # print(f"build_manifests(page_key='{page_key}', page files count={len(page[page_key])}, spaces_dir={address})")
    return manifest_structure, canvas_template
    # return build_manifest(page, spaces_dir, manifest, canvas)

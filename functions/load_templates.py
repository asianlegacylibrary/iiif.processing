import os
import json


m_template = '_manifest_template.json'
c_template = '_canvas_template.json'


def load_templates(python_dir):
    manifest_path = os.path.join(python_dir, m_template)
    canvas_path = os.path.join(python_dir, c_template)

    with open(manifest_path) as template:
        manifest = json.load(template)

    with open(canvas_path, 'r') as canvas_template:
        canvas = json.load(canvas_template)

    # print(type(manifest), manifest['@id'])
    # print(type(canvas), canvas)

    return manifest, canvas

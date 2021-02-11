import os
import json


def load_templates(python_dir, m_template, c_template, s_template):
    manifest_path = os.path.join(python_dir, m_template)
    canvas_path = os.path.join(python_dir, c_template)
    seq_path = os.path.join(python_dir, s_template)

    with open(manifest_path) as template:
        manifest = json.load(template)

    with open(canvas_path, 'r') as canvas_template:
        canvas = json.load(canvas_template)

    with open(seq_path, 'r') as seq_template:
        seq = json.load(seq_template)

    return manifest, canvas, seq

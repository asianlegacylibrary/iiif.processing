from pathlib import Path
import os
import json

from functions import get_image_index, update_canvas_items, update_json_placeholders
from config.config import MANIFEST_ALL_IMAGES, MANIFEST_SAVE_DIR, ACIP_PYTHON_DIR
from templates.placeholder_values import manifest_values


def update_seq(page, seq_template):
    s = seq_template
    item = next(iter(page['images_dict'].values()), None)['viewing']
    if item is not None:
        v = {'viewing': item}
        s = update_json_placeholders(seq_template, v)
    return s


def update_meta(record):
    # Subject, Title, Description, Author, AuthorDate, Commentary, Language, Script, Material,
    # Size_inches, Library, Folios, Publication, Year, Edition,
    meta_listing = []

    for field_name, value in record._asdict().items():
        if value:
            # print(f'{field_name}: {value}')
            meta_listing.append({'label': field_name, 'value': value})

    return meta_listing


def build_manifest(page, manifest_template, canvas_template, seq_template, record):

    record_values = {
        **manifest_values,
        **{
            'manifest_title': record.Title,
            'manifest_description': record.Description
        }
    }

    meta_listing = update_meta(record)

    # with record, fill in the manifest template
    manifest_structure = update_json_placeholders(manifest_template, record_values)

    # quit()
    canvas = []
    sequence = []
    start_page = 1
    image_num = 0

    if 'metadata' in manifest_structure:
        manifest_structure.pop('metadata')
        manifest_structure.update({'metadata': meta_listing})

    if 'sequences' in manifest_structure:
        manifest_structure.pop('sequences')
        sequence.append(update_seq(page, seq_template))
        manifest_structure.update({'sequences': sequence})

        for seq in manifest_structure['sequences']:

            if 'canvases' in seq:
                # delete the canvases list
                seq.pop('canvases')
                # some sources provide inconsistent image names, with no leading zeroes:
                #   like "image-1", "image-11", "image-111" (that can break default image-file ordering).
                # we restore ordering by extracting all trailing digits from image name (could be 1 or more digits),
                #   and sorting the whole list by this extracted number.
                ordered_image_listing = []

                for image_name, meta in page['images_dict'].items():
                    image_ext = Path(image_name).suffix
                    image_num = get_image_index(Path(image_name).stem)
                    image_width = meta['width']
                    image_height = meta['height']
                    ordered_image_listing.append((image_num, image_name, image_ext, image_width, image_height))
                # sort images listing by extracted index:
                ordered_image_listing.sort()

                for image_seq, (image_num, image_name, image_ext, image_width, image_height) in \
                        enumerate(ordered_image_listing, start=start_page):
                    # create canvas for image
                    if MANIFEST_ALL_IMAGES:  # or (start_page <= image_num <= end_page):
                        replacement_items = {
                            "image_name": image_name,
                            "image_seq": image_seq,
                            "image_num": image_num,
                            "width": image_width,
                            "height": image_height,
                            "group_name": page['path']
                        }
                        update_items = update_canvas_items(manifest_values, **replacement_items)
                        current_canvas = update_json_placeholders(canvas_template, update_items)
                        canvas.append(current_canvas)

            seq.update({"canvases": canvas})

    manifest_path = os.path.join(ACIP_PYTHON_DIR, MANIFEST_SAVE_DIR, f'{page["key"]}_p{start_page}_p{image_seq}.json')

    with open(manifest_path, 'w') as m:
        json.dump(manifest_structure, m)

    return manifest_path

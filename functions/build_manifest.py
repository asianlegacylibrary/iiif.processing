from pathlib import Path
import os
import json

from functions import get_image_index, update_canvas_items, update_json_placeholders
from config.config import MANIFEST_ALL_IMAGES, MANIFEST_SAVE_DIR, ACIP_PYTHON_DIR
from templates.placeholder_values import p as placeholder_values


# global_end_page = end_page


# TODO: use this function instead of one below
def build_manifest_alt(spaces_page, manifest_structure, canvas_template):
    # print(spaces_page['images'])

    c = []
    start_page = 1
    image_num = 0
    # global global_end_page
    # end_page = global_end_page
    if 'sequences' in manifest_structure:
        for seq in manifest_structure['sequences']:
            if 'canvases' in seq:
                # delete the canvases list
                seq.pop('canvases')
                # replace with loop over all images in
                for _, image_listing in spaces_page.items():
                    print(image_listing)
                    # some sources provide inconsistent image names, with no leading zeroes:
                    #   like "image-1", "image-11", "image-111" (that can break default image-file ordering).
                    # we restore ordering by extracting all trailing digits from image name (could be 1 or more digits),
                    #   and sorting the whole list by this extracted number.
                    ordered_image_listing = []
                    for image_url in image_listing:
                        image_name = Path(image_url).stem
                        image_num = get_image_index(image_name)
                        ordered_image_listing.append((image_num, image_name, image_url))
                    # sort images listing by extracted index:
                    ordered_image_listing.sort()

                    # now iterate over the sorted image list.
                    for image_seq, (image_num, image_name, image_url) in enumerate(ordered_image_listing, start=start_page):
                        # create canvas for image
                        if MANIFEST_ALL_IMAGES:  # or (start_page <= image_num <= end_page):
                            replacement_items = {
                                "image_url": image_url,
                                "image_name": image_name,
                                "image_seq": image_seq,
                                "image_num": image_num,
                                "group_name": ''
                            }
                            update_items = update_canvas_items(placeholder_values, **replacement_items)
                            current_canvas = update_json_placeholders(canvas_template, update_items)
                            c.append(current_canvas)

                seq.update({"canvases": c})

    # print(json.dumps(manifest, indent=4))

    # if MANIFEST_ALL_IMAGES:
    #     global_end_page = image_num

    # print(end_page)
    # print(spaces_dir)

    # new_manifest = os.path.join(ACIP_PYTHON_DIR, MANIFEST_SAVE_DIR,
    #                             f'{spaces_dir}_p{start_page}_p{global_end_page}.json')
    new_manifest = os.path.join(ACIP_PYTHON_DIR, MANIFEST_SAVE_DIR,
                                f'{spaces_page["key"]}_p{start_page}_p{image_seq}.json')
    print(new_manifest)

    with open(new_manifest, 'w') as m:
        json.dump(manifest_structure, m, indent=4)

    return new_manifest


def build_manifest(page, manifest_structure, canvas_template):
    # print(page)
    c = []
    start_page = 1
    image_num = 0
    if 'sequences' in manifest_structure:
        for seq in manifest_structure['sequences']:
            if 'canvases' in seq:
                # delete the canvases list
                seq.pop('canvases')
                # some sources provide inconsistent image names, with no leading zeroes:
                #   like "image-1", "image-11", "image-111" (that can break default image-file ordering).
                # we restore ordering by extracting all trailing digits from image name (could be 1 or more digits),
                #   and sorting the whole list by this extracted number.
                ordered_image_listing = []
                for image_name in page['images']:
                    image_ext = Path(image_name).suffix
                    image_num = get_image_index(Path(image_name).stem)
                    ordered_image_listing.append((image_num, image_name, image_ext))
                # sort images listing by extracted index:
                ordered_image_listing.sort()

                for image_seq, (image_num, image_name, image_ext) in \
                        enumerate(ordered_image_listing, start=start_page):
                    # create canvas for image
                    if MANIFEST_ALL_IMAGES:  # or (start_page <= image_num <= end_page):
                        replacement_items = {
                            "image_name": image_name,
                            "image_seq": image_seq,
                            "image_num": image_num,
                            "group_name": page['path']
                        }
                        update_items = update_canvas_items(placeholder_values, **replacement_items)
                        current_canvas = update_json_placeholders(canvas_template, update_items)
                        c.append(current_canvas)

            seq.update({"canvases": c})

    manifest_path = os.path.join(ACIP_PYTHON_DIR, MANIFEST_SAVE_DIR, f'{page["key"]}_p{start_page}_p{image_seq}.json')

    with open(manifest_path, 'w') as m:
        json.dump(manifest_structure, m)

    return manifest_path


def build_manifest_oldies(page, manifest_structure, canvas_template):
    print(page)
    c = []
    start_page = 1
    image_num = 0
    if 'sequences' in manifest_structure:
        for seq in manifest_structure['sequences']:
            if 'canvases' in seq:
                # delete the canvases list
                seq.pop('canvases')
                # replace with loop over all images in
                for image_seq, image_url in enumerate(page['images'], start=start_page):
                    image_name = Path(image_url).stem
                    image_num = get_image_index(image_name)
                    # print(image_name, image_num)

                    # create canvas for image
                    if MANIFEST_ALL_IMAGES:  # or (start_page <= image_num <= end_page):
                        replacement_items = {
                            "image_url": image_url,
                            "image_name": image_name,
                            "image_seq": image_seq,
                            "image_num": image_num,
                            "group_name": page['path']
                        }
                        update_items = update_canvas_items(placeholder_values, **replacement_items)
                        current_canvas = update_json_placeholders(canvas_template, update_items)
                        c.append(current_canvas)

            seq.update({"canvases": c})

    manifest_path = os.path.join(ACIP_PYTHON_DIR, MANIFEST_SAVE_DIR, f'{page["key"]}_p{start_page}_p{image_seq}.json')

    with open(manifest_path, 'w') as m:
        json.dump(manifest_structure, m)

    return manifest_path
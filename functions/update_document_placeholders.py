from urllib.parse import quote


def update_canvas_items(placeholder_values, **kwargs):
    identifier = quote(f"{kwargs['group_name']}/{kwargs['image_name']}", safe='')

    return dict(
        identifier=identifier,
        image_name=kwargs['image_name'],
        image_seq=kwargs['image_seq'],
        image_num=kwargs['image_num'],
        width=int(kwargs['width']),
        height=int(kwargs['height']),
        group_name=kwargs['group_name'],
        **placeholder_values
    )


def update_sequence(placeholder_values, **kwargs):
    return dict(
        viewing=kwargs['viewing'],
        **placeholder_values
    )


def update_json_placeholders(template, replacement_items):
    # print('replace?', replacement_items)
    # print('template is', template)
    obj = {}

    for key, value in template.items():
        if isinstance(value, dict):
            obj[key] = update_json_placeholders(value, replacement_items)
        elif isinstance(value, list):
            new_list = []
            for item in value:
                d = update_json_placeholders(item, replacement_items)
                new_list.append(d)
            obj[key] = new_list
        else:
            if key in replacement_items:
                obj[key] = replacement_items[key]
            else:
                obj[key] = value % replacement_items

    return obj

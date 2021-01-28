def update_canvas_items(placeholder_values, **kwargs):
    return dict(
        identifier=f"{kwargs['group_name']}%2F{kwargs['image_name']}",
        image_name=kwargs['image_name'],
        image_seq=kwargs['image_seq'],
        image_num=kwargs['image_num'],
        group_name=kwargs['group_name'],
        **placeholder_values
    )


def update_json_placeholders(template, replacement_items):
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
        elif isinstance(value, int):
            if key in ['width', 'height'] and key in replacement_items:
                obj[key] = replacement_items[key]
            else:
                print('found an int value not in width or height')
        else:
            obj[key] = value % replacement_items
    return obj

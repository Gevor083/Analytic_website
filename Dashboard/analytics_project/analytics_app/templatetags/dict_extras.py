from django import template
import json

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Safely get an item from a mapping-like object.

    If `dictionary` is a JSON string, attempt to parse it. If it's a dict, return dictionary.get(key).
    Return None on any failure instead of raising attribute errors (so templates won't break).
    """
    try:
        # If a JSON string was passed, try to parse it
        if isinstance(dictionary, str):
            try:
                parsed = json.loads(dictionary)
            except Exception:
                return None
            dictionary = parsed
        if isinstance(dictionary, dict):
            return dictionary.get(key)
        # If it's a list of dicts, try to find a dict with matching key (not typical but safe)
        if isinstance(dictionary, list):
            for item in dictionary:
                if isinstance(item, dict) and key in item:
                    return item.get(key)
        return None
    except Exception:
        return None

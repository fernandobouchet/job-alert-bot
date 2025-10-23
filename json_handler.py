import json
import os

DATA_DIR = "data"


def load_json(filepath):
    """
    Loads data from a JSON file.
    Returns an empty list if the file doesn't exist or is invalid.
    """
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load {filepath}. Returning empty list. Error: {e}")
        return []


def save_json(data, filepath):
    """
    Saves data to a JSON file, overwriting it if it exists.
    """
    dir_name = os.path.dirname(filepath)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

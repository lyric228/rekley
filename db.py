from json import dump, load, JSONDecodeError
from os.path import exists as file_exists


def save_json(data: dict, filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as file:
        dump(data, file, ensure_ascii=False, indent=4)


def load_json(filename: str) -> dict:
    try:
        if not file_exists(filename):
            with open(filename, "w", encoding="utf-8") as file:
                dump({}, file, ensure_ascii=False, indent=4)
            return {}
        
        with open(filename, "r", encoding="utf-8") as file:
            return load(file)
        
    except JSONDecodeError:
        save_json({}, filename)
        return {}
    
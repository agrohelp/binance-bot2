# core/force.py

import json
import os

FORCE_FILE = "force.json"

def load_force():
    """Wczytuje wymuszone sygnały z pliku force.json."""
    if not os.path.exists(FORCE_FILE):
        return {"buy": False, "sell": False}

    try:
        with open(FORCE_FILE, "r") as f:
            return json.load(f)
    except:
        return {"buy": False, "sell": False}


def save_force(buy=False, sell=False):
    """Zapisuje wymuszone sygnały."""
    data = {"buy": buy, "sell": sell}
    with open(FORCE_FILE, "w") as f:
        json.dump(data, f, indent=4)


def clear_force():
    """Czyści wymuszone sygnały."""
    save_force(False, False)

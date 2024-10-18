from mtg_script.lib import ScryfallCache, query_scryfall, get_otag
import pandas as pd
import json
import sys

def load_keyfile(fname):
    with open(fname) as f:
        return json.load(f)

def main():
    keyfile = sys.argv[1]

    keys = load_keyfile(keyfile)

    for otag in keys['base_tags']:
        with ScryfallCache(otag, []) as tagged_cards:
            if not tagged_cards:
                tagged_cards.extend(card['name'] for card in get_otag(otag))

    for name, query in keys['custom_tags'].items():
        with ScryfallCache(name, []) as tagged_cards:
            if not tagged_cards:
                tagged_cards.extend(card['name'] for card in query_scryfall(query))


if __name__ == '__main__':
    main()

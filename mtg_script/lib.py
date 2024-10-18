from genericpath import isfile
import requests as req
import json
from itertools import islice

def batched(iterable, n):
    "Batch data into tuples of length n. The last batch may be shorter."
    # batched('ABCDEFG', 3) --> ABC DEF G
    it = iter(iterable)
    while True:
        batch = tuple(islice(it, n))
        if not batch:
            return
        yield batch

def cardlist(df, name):
    s = f"[{name}]"
    s += '\n'.join(f"{row['Name']} ({row['Set code']}) {row['Collector number']}" for _, row in df.iterrows () for _ in range(row['Quantity']))
    return s

def get_otag(otag, page=1):
    for x in query_scryfall(f"otag:{otag}", page):
        yield x

def query_scryfall(query, page=1):
    params = {'q': f"({query}) game:paper", 'page':page}
    resp = req.get('https://api.scryfall.com/cards/search', params=params)
    if resp.ok:
        parsed = resp.json()
        print(f"Received query {query} page {page}")
        for card in parsed['data']:
            yield card
        while parsed['has_more']:
            for card in query_scryfall(query, page+1):
                yield card
    else:
        print(f"Response error: {resp.content}")

def set_release_date(set_code):
    resp = req.get(f'https://api.scryfall.com/sets/{set_code}')
    if resp.ok:
        return resp.json()['released_at']
    else:
        print(f'Response error for set code {set_code}: {resp.content}')

def parse_types(typeline):
    mdfc_parts = typeline.split('//')
    back_types = []
    back_subtypes = []
    permanent_types = ['Land', 'Creature', 'Artifact', 'Enchantment', 'Planeswalker', 'Battle']
    non_permanent_types = ['Instant', 'Sorcery']
    def parse_one_side(typeline):
        type_parts = list(map(lambda t: t.strip().split(), typeline.strip().split('—')))
        types = []
        subtypes = []
        if len(type_parts) == 1:
            types = type_parts[0]
        elif len(type_parts) == 2:
            types, subtypes = type_parts
        else:
            print("Unexpected typeline: {}".format(typeline))
        permanent_type = [t for t in types if t in permanent_types]
        non_permanent_type = [t for t in types if t in non_permanent_types]
        is_permanent = False
        if permanent_type:
            is_permanent = True
        if not permanent_type and not non_permanent_type:
            print(f"Error parsing typeline: {typeline}")
        if not permanent_type and not non_permanent_type:
            print("Missing type for typeline: {}".format(typeline))
        is_historic =  permanent_type == 'Artifact' or 'Legendary' in types or 'Saga' in subtypes
        is_legendary = 'Legendary' in types
        is_creature = 'Creature' in types
        is_artifact = 'Artifact' in types
        return (types, subtypes, is_permanent, is_historic, is_legendary, is_creature, is_artifact)

    if len(mdfc_parts) != 1:
        is_mdfc = True

        front_types, front_subtypes, perm_0, hist_0, leg_0, creat_0, artif_0 = parse_one_side(mdfc_parts[0])
        back_types, back_subtypes, perm_1, hist_1, leg_1, creat_1, artif_1 = parse_one_side(mdfc_parts[1])
        is_permanent = perm_0 or perm_1
        is_historic = hist_0 or hist_1
        is_legendary = leg_0 or leg_1
        is_creature = creat_0 or creat_1
        is_artifact = artif_0 or artif_1
    else:
        is_mdfc = False
        front_types, front_subtypes, is_permanent, is_historic, is_legendary, is_creature, is_permanent = parse_one_side(typeline)


    return {'is_permanent':is_permanent,
        'is_dual_face': is_mdfc,
        'is_historic':is_historic,
        'is_legendary':is_legendary,
        'is_creature':is_creature,
        'is_permanent':is_permanent,
        'front_types':front_types,
        'front_subtypes':front_subtypes,
        'back_types':back_types,
        'back_subtypes':back_subtypes,
    }

def frameable(card):
    new_card = {}
    remap = {'id': 'Scryfall ID'}
    copy_over = ['mana_cost', 'cmc', 'type_line', 'oracle_text', 'power', 'toughness', 'colors', 'rarity'
        'color_identity', 'keywords', 'legalities', 'games', 'reserved', 'edhrec_rank', 'penny_rank', 'produced_mana']
    for before, after in remap.items():
        new_card[after] = card[before]
    for key in copy_over:
        if key in card:
            new_card[key] = card[key]
        elif 'card_faces' in card:
            front, back = card['card_faces']
            if key in front:
                new_card[key] = front[key]
            if key in back:
                new_card['back_' + key] = back[key]
    if 'image_uris' in card:
        new_card['uri'] = card['image_uris']['border_crop']
    else:
        new_card['uri'] = card['card_faces'][0]['image_uris']['border_crop']
    new_card.update(parse_types(card['type_line']))
    return new_card


class ComputedDict(dict):
    def __init__(self, compute_func):
        super().__init__()
        self.compute_func = compute_func


    def __missing__(self, key):
        """Called when a key is not found in the dictionary"""
        value = self.compute_func(key)
        self[key] = value
        return value

    def __getitem__(self, key):
        """Override get item to handle missing keys"""
        try:
            return super().__getitem__(key)
        except KeyError:
            return self.__missing__(key)
            import json
            from typing import Any, TextIO

class ScryfallCache:

    def __init__(self, cache, default={}):
        self.fname = f'scryfall_db/{cache}.json'
        self.file = None
        self.data = None
        self.default = default

    def __enter__(self):
        """
        Open and read the JSON file, returning the parsed data.

        Returns:
            The parsed JSON data as Python objects

        Raises:
            JSONDecodeError: If the file contains invalid JSON
        """
        if isfile(self.fname):
            self.file = open(self.fname, 'r', encoding='utf-8')
            self.data = json.load(self.file)
            self.file.close()
        else:
            self.data = self.default
        return self.data

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Write the modified data back to the JSON file.

        The file is written only if no exception occurred during the context.
        """
        if exc_type is None:  # Only write if no exception occurred
            with open(self.fname, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4)
        return False  # Don't suppress any exceptions

import pandas as pd
import requests as req
import json
from itertools import islice
import sys

def batched(iterable, n):
    "Batch data into tuples of length n. The last batch may be shorter."
    # batched('ABCDEFG', 3) --> ABC DEF G
    it = iter(iterable)
    while True:
        batch = tuple(islice(it, n))
        if not batch:
            return
        yield batch

df = pd.read_csv('ManaBox_Collection.csv')

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
    copy_over = ['mana_cost', 'cmc', 'type_line', 'oracle_text', 'power', 'toughness', 'colors',
        'color_identity', 'keywords', 'legalities', 'games', 'reserved', 'edhrec_rank', 'penny_rank']
    for before, after in remap.items():
        new_card[after] = card[before]
    for key in copy_over:
        if key in card:
            new_card[key] = card[key]
    new_card.update(parse_types(card['type_line']))
    return new_card

def get_scryfall_data(cards):
    # scryfall = []
    for idx, batch in enumerate(batched(cards["Scryfall ID"], 75)):
        formatted_batch = {'identifiers':[{'id':sid} for sid in batch]}
        response = req.post("https://api.scryfall.com/cards/collection", json=formatted_batch)
        #print(json.dumps(json.loads(response.content), indent=2))
        if response.ok:
            response = json.loads(response.content)
            if response['not_found']:
                not_found = ",".join(response['not_found'])
                print(f"Not found Ids: {not_found}")
            for card in map(frameable, response['data']):
                yield card
                # scryfall.append(card)
        else:
            print(f"Response error: {response.content}")
        print(f"Completed batch {idx}")
    # return scryfall

def cardlist(df, name):
    s = f"[{name}]"
    s += '\n'.join(f"{row['Name']} ({row['Set code']}) {row['Collector number']}" for _, row in df.iterrows () for _ in range(row['Quantity']))
    return s

def rare(df):
    return df[df['Purchase price'] >= 2.0]

if __name__ == '__main__':
    infile = sys.argv[1]
    outfile = sys.argv[2]
    basic_lands = 'Plains Island Swamp Mountain Forest'.split()
    df = pd.read_csv(infile)
    df = df[~df['Name'].isin(basic_lands)]
    pd.DataFrame.from_records([x for x in get_scryfall_data(df)]).to_csv(outfile, index=False)

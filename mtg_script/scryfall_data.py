import pandas as pd
import requests as req
import json
import sys
from mtg_script.lib import frameable, batched



def get_scryfall_data(cards):
    # scryfall = []
    for idx, batch in enumerate(batched(cards["Scryfall ID"].unique(), 75)):
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


def main():
    infile = sys.argv[1]
    outfile = sys.argv[2]
    basic_lands = 'Plains Island Swamp Mountain Forest'.split()
    df = pd.read_csv(infile)
    df = df[~df['Name'].isin(basic_lands)]
    pd.DataFrame.from_records([x for x in get_scryfall_data(df)]).to_csv(outfile, index=False)

if __name__ == '__main__':
    main()

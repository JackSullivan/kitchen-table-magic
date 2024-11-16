import sys
import numpy as np
import pandas as pd
from glob import glob
from mtg_script.lib import prep_and_combine, BANLIST

def rare(df):
    return (df.Rarity != 'common') & (df.Rarity != 'uncommon') | (df['Purchase price'] >= 5.0)

def uncommon(df):
    return (df.Rarity != 'common')

def common(df):
    return len(df) * [True]

# HACK Pulled from sample_pools, should go in lib
def pull_card(df, filter, sample_dist=None):
    card = df[filter].sample(weights=sample_dist)
    if len(card) != 1:
        print(f"Expected to sample exactly one card for filter, but got {card}")
    df.drop(card.index, inplace=True)
    return card

def make_booster(df):
    pack = pd.DataFrame()

    collation = [rare] + (3 * [uncommon]) + (5 * [common])
    for filter in collation:
        pack = pd.concat([pack, pull_card(df, filter)])
    return pack

def map_set_code(sc):
    sc = sc.upper()
    if sc == 'PLST':
        sc = 'MB1'
    return sc

def main():
    _, manabox, scryfall, num_players = sys.argv

    num_players = int(num_players)

    np.random.seed(12345)

    drafts = glob('*-draft.tsv')
    draft_formats = [pd.read_csv(f, sep='\t') for f in drafts]

    merg = prep_and_combine(pd.read_csv(manabox), pd.read_csv(scryfall), banlist=BANLIST, exclude_commander=True, draft_formats=draft_formats)

    for booster_num in range(5 * num_players):
        for _, card in make_booster(merg).iterrows():
            # print('1 {} ({}) {}'.format(card.Name, card['Set code'], card['Collector number']))
            print('1 {} ({})'.format(card.Name, map_set_code(card['Set code']), card['Collector number']))
        print()

if __name__ == '__main__':
    main()

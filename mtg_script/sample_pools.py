import pandas as pd
import numpy as np
from mtg_script.lib import get_otag, batched
from mtg_script.web import img,div,html,head,body,style,css, h1,h2
import re
import sys
from math import floor
from glob import glob

def top_drafted(df_17, pct=0.2):
    return df_17.sort_values(by='ALSA')[:floor(len(df_17) * pct)].Name.to_list()

def rare(df):
    edhq = df.edhrec_rank.quantile(0.05)
    prq = df.penny_rank.quantile(0.05)
    return ((df['Purchase price'] >= 5.0) | (df.edhrec_rank <= edhq) | (df.penny_rank <= prq) | (df.is_top_drafted)) & (df.Rarity != 'common')

def uncommon(df):
    return (~rare(df) | df.is_top_drafted) & (df.Rarity != 'common')

def common(df):
    return (~rare(df) | df.is_top_drafted) & ~uncommon(df)

def is_land(df):
    return df.front_types.map(lambda x: 'Land' in x)

def is_artifact(df):
    return df.front_types.map(lambda x: 'Artifact' in x)

def pull_card(df, filter, sample_dist=None):
    card = df[filter].sample(weights=sample_dist)
    if len(card) != 1:
        print(f"Expected to sample exactly one card for filter, but got {card}")
    df.drop(card.index, inplace=True)
    return card

def sample_pack(df):
    """This mutates the input df and returns the pack"""
    pack = pd.DataFrame()

    downsample_kld_block = (2*(~df['Set code'].isin(['KLD', 'AER'])))+1
    pack = pd.concat([pack, pull_card(df, rare)])
    for _ in range(4):
        pack = pd.concat([pack, pull_card(df, uncommon)])
    for color in 'W U B R G'.split():
        filter = lambda df: common(df) & (df.colors.map(lambda x: color in x))
        pack = pd.concat([pack, pull_card(df, filter, downsample_kld_block)])
    while pack.is_creature.sum() < 3:
        filter = lambda df: common(df) & (df.is_creature)
        pack = pd.concat([pack, pull_card(df, filter, downsample_kld_block)])
    if is_artifact(pack).sum() < 1:
        filter = lambda df: common(df) & is_artifact(df)
        pack = pd.concat([pack, pull_card(df, filter, downsample_kld_block)])
    if is_land(pack).sum() < 1:
        filter = lambda df: common(df) & is_land(df)
        pack = pd.concat([pack, pull_card(df, filter)])
    while len(pack) < 15:
        pack = pd.concat([pack, pull_card(df, common, downsample_kld_block)])

    return pack


BANLIST = ['Sol Ring']

def prep_and_combine(df, sf, draft_formats = []):
    df = df.loc[df.index.repeat(df.Quantity)]
    df = df.drop('Quantity', axis=1)
    basic_lands = 'Plains Island Swamp Mountain Forest'.split()
    df = df[~df['Name'].isin(basic_lands)]
    df = df[~df.Name.isin(BANLIST)]

    df = df[df['Binder Type'] == 'binder']

    is_top_drafted = [card for draft in draft_formats for card in top_drafted(draft, 0.2)]

    df['is_top_drafted'] = df.Name.isin(is_top_drafted)

    commander_matters = [c['name'] for c in get_otag('commander-matters')]

    df = df[~df.Name.isin(commander_matters)]

    return df.merge(sf, how='left', on='Scryfall ID')

def card_binder_pool_grid(cards, binder_col, pool_col, by_pools=False):
    binders = list(sorted(cards[binder_col].unique()))
    pools = list(sorted(cards[pool_col].unique()))
    styl=style(css(
        '.binder_container > div', {'padding': '10px',
            'border-radius': '5px',
            'border-color':'black',
            'border':'solid',
            'width':'100%'},
        '.binder_container', {'display':'grid'},
        '.binder_pool_cards', {
            'display':'grid',
            'grid-template-columns':'repeat(6, 1fr)',
            'grid-auto-flow':'row',
            'border-radius': '5px',
            'border-color': 'green',
            'border':'solid'},
        '.card', {'object-fit':'contain', 'max-width': '100%', 'height': 'auto', },#'grid-row':2},
        'h1', {'grid-row':1},
        'h2', {'grid-row':1, 'grid-column': '1 / 7'}))

    binders_html = []

    for binder in binders:
        binder_html = [h1(f'Binder {binder}')]
        binder_filter = cards[binder_col] == binder
        if by_pools:
            for pool in pools:
                filter = binder_filter & (cards[pool_col] == pool)
                pool_html = [h2(pool)]
                for _, card in cards[filter].sort_values('cn_ord').iterrows():
                    pool_html.append(img(None, src=card.uri, alt=card.Name, clazz='card'))
                binder_html.append(div(pool_html, clazz=f'binder_pool_cards {pool}'))
        else:
            filter = binder_filter & (cards[pool_col].isin(pools))
            for _, card in cards[filter].sort_values('cn_ord').iterrows():
                binder_html.append(img(None, src=card.uri, alt=card.Name, clazz='card'))
        binders_html.append(div(binder_html, clazz=f'binder binder_{binder}'))


    res = div(binders_html, clazz='binder_container')

    res = html([head(styl), body(res)])

    return res


def sealed_pools(df, num_pools=5, format_str="pool_{}"):
    pools = pd.DataFrame()
    for _ in range(6):
        for idx in range(num_pools):
            pack = sample_pack(df)
            pack['pool'] = [format_str.format(idx)] * len(pack)
            pools = pd.concat([pools, pack])
    return pools

cnre = re.compile('(?:[a-zA-Z]*)-?(\d+)(?:\w*)')
def collector_number_sort(cn):
    mtc = cnre.match(cn)
    if not mtc:
        print(f"failed to match collector number: {cn}")
    return int(mtc[1])

def main():
    _, manabox, scryfall = sys.argv

    np.random.seed(12345)

    drafts = glob('*-draft.tsv')
    draft_formats = [pd.read_csv(f, sep='\t') for f in drafts]

    merg = prep_and_combine(pd.read_csv(manabox), pd.read_csv(scryfall), draft_formats)
    merg['cn_ord'] = merg['Collector number'].map(collector_number_sort)

    pools = sealed_pools(merg, 5)

    pools = pools.sort_values(by=['Binder Name', 'pool', 'cn_ord'])#[['Binder Name', 'pool', 'Name', 'Collector number', 'uri']]# .to_csv(sys.stdout, sep="\t", index=False)

    for pool, cards in pools.groupby('pool'):
        pool_str = '\n'.join(
            "1 {} ({}) [{}]".format(card.Name, card['Set code'], card['Collector number'])
            for _, card in cards.iterrows())
        with open(f'{pool}.dec', 'w') as f:
            f.write(pool_str)

    with open('by_binder.html', 'w') as f:
        f.write(card_binder_pool_grid(pools, 'Binder Name', 'pool'))

    with open('by_pool.html', 'w') as f:
        f.write(card_binder_pool_grid(pools, 'Binder Name', 'pool', True))

if __name__ == '__main__':
    main()

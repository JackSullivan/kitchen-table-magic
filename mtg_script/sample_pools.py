import pandas as pd
import numpy as np
from mtg_script.lib import get_otag, batched
from mtg_script.web import img,div,html,head,body,style,css, h1,h2,tr,td, table, thead, tbody, th
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

    commander_matters = set([c['name'] for c in get_otag('commander-matters')]
        + [c['name'] for c in get_otag('synergy-commander')])

    df = df[~df.Name.isin(commander_matters)]

    return df.merge(sf, how='left', on='Scryfall ID')

colorord = {c:v for v,c in enumerate('W U B R G'.split())}
def colorsort(c):
    if isinstance(c, float):
        return 100
    c = eval(c)
    if len(c) == 1 and c[0] in colorord:
        return colorord[c[0]]
    elif len(c) > 1:
        return 10
    return 1000


common_style = style(css(
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

def card_binder_pool_grid(cards, binder_col, pool_col, by_pools=False):
    binders = list(sorted(cards[binder_col].unique()))
    pools = list(sorted(cards[pool_col].unique()))

    binders_html = []

    for binder in binders:
        binder_html = [h1(f'Binder {binder}')]
        binder_filter = cards[binder_col] == binder
        sort_cols = ['Set code', 'cn_ord']
        if binder == "Old Border":
            sort_cols = ['color_ord', 'Name'] + sort_cols
        if by_pools:
            for pool in pools:
                filter = binder_filter & (cards[pool_col] == pool)
                pool_html = [h2(pool)]
                for _, card in cards[filter].sort_values(sort_cols).iterrows():
                    pool_html.append(img(None, src=card.uri, alt=card.Name, clazz='card'))
                binder_html.append(div(pool_html, clazz=f'binder_pool_cards {pool}'))
        else:
            filter = binder_filter & (cards[pool_col].isin(pools))
            for _, card in cards[filter].sort_values(sort_cols).iterrows():
                binder_html.append(img(None, src=card.uri, alt=card.Name, clazz='card', onClick="this.style.display = 'none'"))
        binders_html.append(div(binder_html, clazz=f'binder binder_{binder}'))


    res = div(binders_html, clazz='binder_container')

    res = html([head(common_style), body(res)])

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

def display_overlaps(overlap):
    styl = style("""
        table {
          border-collapse: collapse;
          border: 2px solid rgb(140 140 140);
          font-family: sans-serif;
          font-size: 0.8rem;
          letter-spacing: 1px;
        }

        caption {
          caption-side: bottom;
          padding: 10px;
          font-weight: bold;
        }

        thead,
        tfoot {
          background-color: rgb(228 240 245);
        }

        th,
        td {
          border: 1px solid rgb(160 160 160);
          padding: 8px 10px;
        }

        td:last-of-type {
          text-align: center;
        }

        tbody > tr:nth-of-type(even) {
          background-color: rgb(237 238 242);
        }

        tfoot th {
          text-align: right;
        }

        tfoot td {
          font-weight: bold;
        }

        """)
    exploded = overlap.explode('binder_counts')
    binders = sorted(exploded.binder_counts.unique().tolist())

    binder_html = []
    for binder in binders:
        hdr = h2(binder)
        theader = thead(tr([th("Name"), th("Set"), th('CN'), th("Target Binder")]))
        rows = []
        for id, card in exploded[exploded.binder_counts == binder].iterrows():
            rows.append(tr([
                td(card.Name),
                td(card['Set code']),
                td(card['Collector number']),
                td(card['Binder Name'])
            ], clazz=f"card_{id}", onClick=f"for (let el of document.getElementsByClassName('card_{id}')) el.style.display='none';"))
        tbl = table([theader, tbody(rows)])
        binder_html.append(div([hdr, tbl]))
    return(html([head(styl), body(binder_html)]))
    # table_rows = []
    # for _, card in overlap.sort_values(['Binder Name', 'Name']).iterrows():
    #     tr([
    #         td(card.Name),
    #         td(card['Set code'])
    #     ])



def main():
    _, manabox, scryfall = sys.argv

    np.random.seed(12345)

    drafts = glob('*-draft.tsv')
    draft_formats = [pd.read_csv(f, sep='\t') for f in drafts]

    merg = prep_and_combine(pd.read_csv(manabox), pd.read_csv(scryfall), draft_formats)
    merg['cn_ord'] = merg['Collector number'].map(collector_number_sort)
    merg['color_ord'] = merg.colors.map(colorsort)

    amb_col = merg.groupby(['Name', 'Set code', 'Collector number'])['Binder Name'].agg(binder_counts=lambda x: set(x))
    amb_col = amb_col[amb_col.binder_counts.map(len) > 1].reset_index()

    pools = sealed_pools(merg, 5)

    pools = pools.sort_values(by=['Binder Name', 'pool', 'cn_ord'])#[['Binder Name', 'pool', 'Name', 'Collector number', 'uri']]# .to_csv(sys.stdout, sep="\t", index=False)

    for pool, cards in pools.groupby('pool'):

        overlap = amb_col.merge(cards, how='inner', on=['Name', 'Set code', 'Collector number'], suffixes=('_amb', '_pool'))

        with open(f'{pool}_disambiguate.html', 'w') as f:
            f.write(display_overlaps(overlap))
        # print(pool)
        # # print(overlap.columns)
        # print(overlap[['Name', 'Set code', 'Collector number', 'Binder Name', 'binder_counts']].sort_values(['Binder Name', 'Name']))

        pool_str = '\n'.join(
            "1 {} ({}) {}".format(card.Name, card['Set code'], card['Collector number'])
            for _, card in cards.iterrows())
        with open(f'{pool}.dec', 'w') as f:
            f.write(pool_str)

    with open('by_binder.html', 'w') as f:
        f.write(card_binder_pool_grid(pools, 'Binder Name', 'pool'))

    with open('by_pool.html', 'w') as f:
        f.write(card_binder_pool_grid(pools, 'Binder Name', 'pool', True))

if __name__ == '__main__':
    main()

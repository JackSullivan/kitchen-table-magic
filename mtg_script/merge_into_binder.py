import sys
import pandas as pd
from pandas.core.indexes.base import get_group_index_sorter

from mtg_script.lib import prep_and_combine
from mtg_script.web import div, img, style, css, html, head, body, h2

def generate_inserts(src, dest):
    src['clade'] = 'source'
    dest['clade'] = 'destination'
    merg = pd.concat([src, dest])
    sort_cols = ['set_release_date', 'cn_ord']
    merg = merg.sort_values(sort_cols, ascending=False)

    merge_spots = []
    merge_spot = (None, [], None)
    prev_state = 'destination'
    prev_card = None
    for _, card in merg.iterrows():
        match (prev_state, card.clade):
            case ('destination', 'source'):
                merge_spot = (prev_card, merge_spot[1] + [card], None)
            case ('source', 'source'):
                merge_spot[1].append(card)
            case ('source', 'destination'):
                merge_spot = (merge_spot[0], merge_spot[1], card)
                merge_spots.append(merge_spot)
                merge_spot = (None, [], None)
            case ('destination', 'destination'):
                pass
        prev_card = card
        prev_state = card.clade

    return merge_spots

def render_card(card, **kwargs):
    return img(None, src=card.uri, alt=card.Name, clazz='card', **kwargs)

stjle = style(css(
    '.merge > div', {'padding': '10px',
        'border-radius': '5px',
        'border-color':'black',
        'border':'solid',
        'width':'100%',
    },
    '.merge', {
        'display':'grid',
        'grid-template-columns': 'repeat(3, 1fr)',
        'grid-auto-flow':'row'
    },
    # '.before',  {'grid-column': '1 / 3'},
    # '.to_splice',  {'grid-column': '2 / 3'},
    # '.after',  {'grid-column': '3 / 3'},
    'h2', {'grid-row':1, 'grid-column': '1 / 7'},
    '.card', {'object-fit':'contain', 'max-width': '100%', 'height': 'auto'},
))

def render_merge_spot(merge_spot):
    before, cards, after = merge_spot
    return div([
        div([h2("before"), render_card(before)], clazz='before'),
        div(map(render_card, cards), clazz='to_splice'),
        div([h2("after"), render_card(after)], clazz='after'),
    ], clazz='merge')

def main():
    pd.options.mode.copy_on_write = True
    _, manabox, scryfall, src, dest = sys.argv

    merg = prep_and_combine(pd.read_csv(manabox), pd.read_csv(scryfall))

    src = merg[merg['Binder Name'] == src] # & merg.query(query)]
    dest = merg[merg['Binder Name'] == dest]

    inserts = generate_inserts(src, dest)

    print(html([head(stjle), body(map(render_merge_spot, inserts))]))

if __name__ == '__main__':
    main()

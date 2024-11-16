from mtg_script.web import h1,h2, img, div, html, head, body, common_style, script
from mtg_script.lib import prep_and_combine, collector_number_sort, colorsort
import sys
from glob import glob
import pandas as pd

collapsible_js = script("""
    var coll = document.getElementsByClassName("collapsible");
    var i;

    for (i = 0; i < coll.length; i++) {
      coll[i].addEventListener("click", function() {
        this.classList.toggle("active");
        var content = this.nextElementSibling;
        if (content.style.display === "block") {
          content.style.display = "none";
        } else {
          content.style.display = "block";
        }
      });
    }
    """, type='text/javascript')

def binder_sort_sheet(all_cards, binder_col):
    binders = list(sorted(all_cards[binder_col].unique()))
    binders_html = []

    sets = all_cards.sort_values('set_release_date')['Set code'].unique().tolist()

    for binder in binders:
        binder_html = [h1(f'Binder {binder}')]
        sort_cols = ['set_release_date', 'cn_ord']

        for card_set in sets:
            filter = (all_cards[binder_col] == binder) & (all_cards['Set code'] == card_set)
            cards = all_cards[filter].sort_values(sort_cols, ascending=False)
            if len(cards) > 0:
                set_html = [h2(card_set)]
                for _, card in cards.iterrows():
                    set_html.append(img(None, src=card.uri, alt=card.Name, clazz='card', onClick="this.style.display='none'"))
                binder_html.append(div(set_html, clazz='collapsible binder_pool_cards'))


            # if sets_html:
            #     binder_html.append(div(sets_html, clazz='binder_pool_cards'))

        # for _, card in all_cards[filter].sort_values(sort_cols, ascending=False).iterrows():

            # binder_html.append(img(None, src=card.uri, alt=card.Name, clazz='card', onClick="this.style.display = 'none'"))
        binders_html.append(div(binder_html, clazz=f'collapsible binder binder_{binder}'))


    res = div(binders_html, clazz='binder_container')

    res = html([head([common_style, collapsible_js]), body(res)])

    return res

def main():
    _, manabox, scryfall = sys.argv

    drafts = glob('*-draft.tsv')
    draft_formats = [pd.read_csv(f, sep='\t') for f in drafts]

    merg = prep_and_combine(pd.read_csv(manabox), pd.read_csv(scryfall))

    with open('binder_sort_sheet.html', 'w') as f:
        f.write(binder_sort_sheet(merg, 'Binder Name'))

if __name__ == '__main__':
    main()

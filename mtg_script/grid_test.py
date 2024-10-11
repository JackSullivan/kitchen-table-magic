from web import *
from random import randrange
from collections import defaultdict

if __name__ == '__main__':

    binders = [i for i in range(10)]
    pools = [i for i in range(5)]

    cards = defaultdict(list)
    for idx in range(90):
        binder = randrange(10)
        pool = randrange(5)
        cards[(binder,pool)].append(f"Card_{idx}_Binder_{binder}_Pool_{pool}")

    # print(binders)
    # print(pools)
    styl=style(css(
        '.binder_container > div', {'padding': '10px', 'border-radius': '5px'},
        '.binder_container', {'display':'grid'},
        '.binder_pool_cards', {'display':'grid', 'grid-template-columns':f'repeat({len(pools)}, 1fr)'}))

    res =div((div((div(
        (div(card, clazz='card')
            for card
            in cards[(binder, pool)]),
        clazz=f"binder_pool_cards pool_{pool}")
    for pool in pools), clazz=f"binder binder_{binder}")
        for binder in binders
    ), clazz="binder_container")

    res = html([head(styl), body(res)])
    # res = '\n'.join([div((div(card, clazz='card') for card in cards[(binder, pool)]), clazz=f"binder_pool_cards pool_{pool}")
    #     for binder in binders
    #         for pool in pools])
    # binder = 0
    # pool = 0
    # div((div(card, clazz='card') for card in cards[(binder, pool)]), clazz=f"binder_pool_cards {pool}")

    # res = '\n'.join(div(div(div(card, clazz="card"), clazz=f"binder_pool_cards {pool}"), clazz=f"binder {binder}") for binder in binders
    #     for pool in pools
    #         for card in cards[(binder,pool)])
    print(res)

    # for binder in binders:
    #     for pool in pools:
    #         for card in cards[(binder,pool)]:
    #             div(card, clazz="card")

    # div(, clazz="binders")

from mtg_script.lib import query_scryfall
import sys

if __name__ == '__main__':
    query = ' '.join(sys.argv[1:])
    for card in query_scryfall(query):
        print("1 {} ({}) {}".format(card['name'],
            card['set'], card['collector_number'], flush=True))

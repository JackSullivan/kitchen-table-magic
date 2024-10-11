
scryfall_data.csv: ManaBox_Collection.csv
	python mtg_script/scryfall_data.py $< $@


by_binder.html: ManaBox_Collection.csv scryfall_data.csv
	python mtg_script/sample_pools.py $^

scryfall_data.csv: ManaBox_Collection.csv
	python mtg_script/scryfall_data.py $< $@

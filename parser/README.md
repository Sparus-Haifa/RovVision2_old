# parse data
## 1. exports images from record and create a data.csv for every record
## 2. merges all data.csv of every record to a master data.csv of all records
## 3. find matching FLC-FLS pairs and save them in pairs.csv
python3 export_data.py


# create sections.csv
python3 create_sections.py -i bags/pairs.csv

# review pairs and create sections
python3 play_pairs.py -i bags/pairs.csv 


# create chunks of pairs of size 300 in chunks.csv
python3 chunkify.py

# split chunks to train, test and validation
python3 split_chunks.py
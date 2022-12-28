# create a csv where all the pairs are combined from the chunks csv file

import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split

class ChunksParser:
    def __init__(self, csv_path):
        self.csv_path = csv_path

        # check if csv file exists
        if not os.path.exists(self.csv_path):
            print('ERROR: no path to csv')
            print('Usage: python findpairs.py -i [path_to_csv]')
            exit()

        # save path
        self.main_path = os.path.dirname(self.csv_path)
        self.df = pd.read_csv(self.csv_path)

    def combine_chunks(self):
        # df = pd.read_csv(csv_path)
        # print(df.head())

        # load the chunks.csv file
        chunks_df = pd.read_csv(os.path.join(os.path.dirname(self.csv_path), 'chunks.csv'), index_col=0)
        chunks_train_set, chunks_test_set = train_test_split(chunks_df, test_size=0.3)
        chunks_train_set, chunks_validation_set = train_test_split(chunks_train_set, test_size=10 / 70)

        print('chunks_train_set', chunks_train_set.shape)
        print('chunks_validation_set', chunks_validation_set.shape)
        print('chunks_test_set', chunks_test_set.shape)
        print(chunks_train_set.head())

        # parse the chunks
        self.parse_chunks(chunks_train_set, 'pairs_train.csv')
        self.parse_chunks(chunks_validation_set, 'pairs_validation.csv')
        self.parse_chunks(chunks_test_set, 'pairs_test.csv')


    def parse_chunks(self, chunks_df, filename):

        pairs_df = pd.DataFrame(columns=['Index', 'FLC', "FLS", "bagfile", "timestamp_FLC", "timestamp_FLS"])

        # iterate over the chunks
        for index, row in chunks_df.iterrows():
            # get the first and last image
            first_image = row['first_image']
            last_image = row['last_image']
            # print('first_image', first_image)
            # print('last_image', last_image)

            # get the df for this chunk
            chunk_df = self.df[(self.df['Index'] >= first_image) & (self.df['Index'] <= last_image)]
            # print('chunk_df', chunk_df.shape)
            # print(chunk_df.head(100))

            # add the chunk to the pairs_df
            pairs_df = pairs_df.append(chunk_df, ignore_index=True)




            # print('pairs_df', pairs_df.shape)
            # print(pairs_df.head(5))

        # save the pairs to a new csv file
        pairs_df.to_csv(os.path.join(os.path.dirname(csv_path), filename), header=True)



if __name__ == '__main__':
    csv_path = r'bags/pairs.csv'
    chunks_parser = ChunksParser(csv_path)
    chunks_parser.combine_chunks()
    # combine_chunks(csv_path)

    print('done')
import os
import pandas as pd
import numpy as np
import re
from natsort import natsorted
from sklearn.model_selection import train_test_split
from pathlib import Path
import cv2
import matplotlib.pyplot as plt

import argparse


## split data to train, validation and test sets

class PairSplitter:
    def __init__(self, csv_file) -> None:

        self.csv_file = csv_file

        ## check is csv file exists
        if not os.path.exists(self.csv_file):
            print('ERROR: no path to csv')
            print('Usage: python findpairs.py -i [path_to_csv]')
            exit()

        # save path
        self.main_path = os.path.dirname(self.csv_file)



    def split_pairs(self):
        # df_pairs = pd.read_csv(csv_path, index_col=0)
        df_pairs = pd.read_csv(self.csv_file)
        print(df_pairs.head())

        recordings = df_pairs['bagfile'].unique()
        print(recordings)


        # label = []
        # data = []
        # for record in recordings:
        #     label.append(record)
        #     size = (df_pairs['bagfile']==record).sum()
        #     data.append(size)
        #     print(size)
        # # exit()

        # print(label)
        # print(data)



        # plt.pie(data, labels=label, autopct='%1.1f%%', explode=[0,0,0,0.1,0], shadow=True, startangle=90)
        # plt.title('Records')
        # plt.axis('equal')



        # plt.show()
        # exit()

        # init Dataframe for pairs data set

        new_header = df_pairs.iloc[0] #grab the first row for the header

        df_pairs = df_pairs[1:] #take the data less the header row
        df_pairs.columns = new_header #set the header row as the df header


        # print(df_pairs)

        # exit()



    


        # split to train - 0.6, validation - 0.1, test - 0.3 sets
        df_train_set, df_test_set = train_test_split(df_pairs, test_size=0.3)
        df_train_set, df_validation_set = train_test_split(df_train_set, test_size=10 / 70)

        print('Dataset size: ', df_pairs.shape[0])
        print('Train set size: ', df_train_set.shape[0], f'({df_train_set.shape[0]/df_pairs.shape[0]:.0%})')
        print('Validation set size: ', df_validation_set.shape[0], f'({df_validation_set.shape[0]/df_pairs.shape[0]:.0%})')
        print('Test set size: ', df_test_set.shape[0], f'({df_test_set.shape[0]/df_pairs.shape[0]:.0%})')

        # saving csv files
        df_train_set.to_csv(os.path.join(self.main_path, 'train_set.csv'), header=True)
        df_validation_set.to_csv(os.path.join(self.main_path, 'validation_set.csv'), header=True)
        df_test_set.to_csv(os.path.join(self.main_path, 'test_set.csv'), header=True)
        # df_pairs.to_csv(os.path.join(main_path, 'pairs.csv'), header=True)





def main():

    usageDescription = 'finding pairs'

    parser = argparse.ArgumentParser(description='find pairs parser, %s'%usageDescription, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-i', '--csvPath', default=None, help=' path to input csv file ')
    parser.add_argument('-s', '--savePairs', action='store_true', help='save tiffs files to record folder')



    args = parser.parse_args()


    # main_path = r'/workspaces/RovVision2_old'
    main_path = args.csvPath

    save_pairs = args.savePairs

    pair_splitter = PairSplitter(main_path, save_pairs)

    pair_splitter.split_pairs()





    if not main_path:
        print('ERROR: no path to csv')
        print('Usage: python findpairs.py -i [path_to_csv]')
        exit()


    filename = os.path.basename(main_path)
    main_path = os.path.dirname(main_path)


    csv_path = os.path.join(main_path, filename)


    



if __name__=="__main__":
    main()
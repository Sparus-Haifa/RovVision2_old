import os
import pandas as pd
import numpy as np
import re
from natsort import natsorted
from sklearn.model_selection import train_test_split
from pathlib import Path
import cv2

import argparse



class PairFinder:
    def __init__(self, main_path, save_pairs) -> None:

        # print(save_pairs)
        # exit()

        self.main_path = main_path

        self.save_pairs = save_pairs



        if not self.main_path:
            print('ERROR: no path to csv')
            print('Usage: python findpairs.py -i [path_to_csv]')
            exit()


        self.filename = os.path.basename(self.main_path)
        self.main_path = os.path.dirname(self.main_path)


    def extract_digits(self, s):
        return re.split('[_ .]', s)[1]


    def find_type(self, s, relevant_list):
        if s in relevant_list:
            return 1
        else:
            return 0


    def partly_str_in(self, s, relevant_list):
        if s in relevant_list:
            return relevant_list[relevant_list.index(s)]


    def find_closest_index(self, element, other_list):
        return min(other_list, key=lambda x: abs(x - element))


    def change_main_path(self, main_path, path_string, keep_path_locations):
        orig_path = Path(path_string)
        new_path = os.path.join(main_path, *list(orig_path.parts)[keep_path_locations:])

        return new_path


    def find(self):




        # main_path = r'E:\OneDrive - Haifa University\opher\deeperSense\eilat_aug_2021\parsed_bags'
        # main_path = r'/workspaces/bag2video'
        # main_path = r'/workspaces/RovVision2_old'

        csv_path = os.path.join(self.main_path, self.filename)
        # csv_path = os.path.join(main_path, 'image_nav_bagfile_name.csv')


        # data frame for the CSV
        df = pd.read_csv(csv_path)
        # init Dataframe for pairs data set
        df_pairs = pd.DataFrame(columns=['FLC', 'FLS', 'bagfile'])

        # print(df_pairs.head())
        # exit()

        # list of of bag files
        bags_list = list(set(df['bagfile'].to_list()))
        print(bags_list)

     


        # iterating over the bags files
        for bag_ii in bags_list:
            print(bag_ii)
            # df slicing according current bagfile
            df_tmp = df.loc[df['bagfile'] == bag_ii]
            # indices of FLC images
            FLS_idx = df_tmp.index[df_tmp['topic'] == 'topic_sonar'].to_list()
            # print('FLC index')
            # print(FLC_idx)
            # indices of FLS color 2 (jet) images
            FLC_idx = df_tmp.index[df_tmp['topic'] == 'topic_stereo_camera'].to_list()

            # following the smaller amount of files
            if len(FLS_idx) < len(FLC_idx):
                FLC_idx = [self.find_closest_index(element, FLC_idx) for element in FLS_idx]
            else:
                FLS_idx = [self.find_closest_index(element, FLS_idx) for element in FLC_idx]

            df_FLC = df_tmp.loc[FLC_idx]['value']
            df_FLS = df_tmp.loc[FLS_idx]['value']
            df_Bag = df_tmp.loc[FLC_idx]['bagfile']
            
            

            # changing paths to local main path
            # df_FLC = df_FLC.apply(lambda x: change_main_path(main_path=main_path, path_string=x, keep_path_locations=-3))
            # df_FLS = df_FLS.apply(lambda x: change_main_path(main_path=main_path, path_string=x, keep_path_locations=-3))

            # appending pairs datafame
            df_pairs = pd.concat([df_pairs, pd.DataFrame({'FLC': df_FLC.to_list(),
                                                        'FLS': df_FLS.to_list(),
                                                        'bagfile': df_Bag.to_list()
                                                        })], ignore_index=True)

            # df_pairs = df_pairs.reset_index().rename(columns={'index': 'Index'})

        # add header to the index column
        df_pairs = df_pairs.rename_axis('Index', axis='index')



    


        if self.save_pairs:

            # # split to train - 0.6, validation - 0.1, test - 0.3 sets
            # df_train_set, df_test_set = train_test_split(df_pairs, test_size=0.3)
            # df_train_set, df_validation_set = train_test_split(df_train_set, test_size=10 / 70)

            # print('Dataset size: ', df_pairs.shape[0])
            # print('Train set size: ', df_train_set.shape[0], f'({df_train_set.shape[0]/df_pairs.shape[0]:.0%})')
            # print('Validation set size: ', df_validation_set.shape[0], f'({df_validation_set.shape[0]/df_pairs.shape[0]:.0%})')
            # print('Test set size: ', df_test_set.shape[0], f'({df_test_set.shape[0]/df_pairs.shape[0]:.0%})')

            # # saving csv files
            # df_train_set.to_csv(os.path.join(self.main_path, 'train_set.csv'), header=True)
            # df_validation_set.to_csv(os.path.join(self.main_path, 'validation_set.csv'), header=True)
            # df_test_set.to_csv(os.path.join(self.main_path, 'test_set.csv'), header=True)
            df_pairs.to_csv(os.path.join(self.main_path, 'pairs.csv'), header=True)




def main():

    usageDescription = 'finding pairs'

    parser = argparse.ArgumentParser(description='find pairs parser, %s'%usageDescription, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-i', '--csvPath', default=None, help=' path to input csv file ')
    parser.add_argument('-s', '--savePairs', action='store_true', help='save tiffs files to record folder')



    args = parser.parse_args()


    # main_path = r'/workspaces/RovVision2_old'


    pair_finder = PairFinder(main_path=args.csvPath, save_pairs=args.savePairs)
    pair_finder.find()
   



if __name__=="__main__":
    main()
import os
import pandas as pd
import numpy as np
import re
from natsort import natsorted
from sklearn.model_selection import train_test_split
from pathlib import Path
import cv2

import argparse

usageDescription = 'finding pairs'

parser = argparse.ArgumentParser(description='find pairs parser, %s'%usageDescription, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-i', '--csvPath', default=None, help=' path to input csv file ')
args = parser.parse_args()


# main_path = r'/workspaces/RovVision2_old'
main_path = args.csvPath

FLS_window_name = 'FLS_image'
FLC_window_name = 'FLC_image'


curDelay = 0
highSpeed = False


if not main_path:
    print('ERROR: no path to csv')
    print('Usage: python findpairs.py -i [path_to_csv]')
    exit()


filename = os.path.basename(main_path)
main_path = os.path.dirname(main_path)



def extract_digits(self):
    return re.split('[_ .]', self)[1]


def find_type(s, relevant_list):
    if s in relevant_list:
        return 1
    else:
        return 0


def partly_str_in(s, relevant_list):
    if s in relevant_list:
        return relevant_list[relevant_list.index(s)]


def find_closest_index(element, other_list):
    return min(other_list, key=lambda x: abs(x - element))


def change_main_path(main_path, path_string, keep_path_locations):
    orig_path = Path(path_string)
    new_path = os.path.join(main_path, *list(orig_path.parts)[keep_path_locations:])

    return new_path


# main_path = r'E:\OneDrive - Haifa University\opher\deeperSense\eilat_aug_2021\parsed_bags'
# main_path = r'/workspaces/bag2video'
# main_path = r'/workspaces/RovVision2_old'

csv_path = os.path.join(main_path, filename)
# csv_path = os.path.join(main_path, 'image_nav_bagfile_name.csv')


# data frame for the CSV
df = pd.read_csv(csv_path)
# init Dataframe for pairs data set

# df_pairs = pd.DataFrame(columns=['FLC', 'FLS'])
# print(df_pairs)

# list of of bag files
# bags_list = list(set(df['bagfile'].to_list()))
# print(bags_list)


# iterating over the bags files
# for bag_ii in bags_list:
    # print(bag_ii)
    # df slicing according current bagfile

    # df_tmp = df.loc[df['bagfile'] == bag_ii]

    # # indices of FLC images
    # FLC_idx = df_tmp.index[df_tmp['topic'] == 'topic_sonar'].to_list()
    # # print('FLC index')
    # # print(FLC_idx)
    # # indices of FLS color 2 (jet) images
    # FLS_idx = df_tmp.index[df_tmp['topic'] == 'topic_stereo_camera'].to_list()

    # # following the smaller amount of files
    # if len(FLS_idx) < len(FLC_idx):
    #     FLC_idx = [find_closest_index(element, FLC_idx) for element in FLS_idx]
    # else:
    #     FLS_idx = [find_closest_index(element, FLS_idx) for element in FLC_idx]

    # df_FLC = df_tmp.loc[FLC_idx]['label']
    # df_FLS = df_tmp.loc[FLS_idx]['label']

    # # changing paths to local main path
    # df_FLC = df_FLC.apply(lambda x: change_main_path(main_path=main_path, path_string=x, keep_path_locations=-3))
    # df_FLS = df_FLS.apply(lambda x: change_main_path(main_path=main_path, path_string=x, keep_path_locations=-3))

    # # appending pairs datafame
    # df_pairs = pd.concat([df_pairs, pd.DataFrame({'FLC': df_FLC.to_list(),
    #                                               'FLS': df_FLS.to_list()})], ignore_index=True)

    # print(df_pairs)
# for index, row in df.iterrows():
index = 0
# for index in
while 0 <= index <= len(df): 
    row = df.iloc[index]
    print(row['FLC'], row['FLS'])
    flc, fls = (row['FLC'], row['FLS'])
    # print(row)
    flc_img = cv2.imread(flc)
    cv2.imshow('FLC_window_name', flc_img)

    fls_img = cv2.imread(fls)
    cv2.imshow('FLS_window_name', fls_img)


    print("wait key")
    key = cv2.waitKey(curDelay)&0xff
    # key = cv2.waitKey(0)
    if key == ord('q') or key == 27:
        print('quit')
        break
    elif key == ord(' '):
        print('space')
        curDelay = 0
    elif key == ord('+'):
        print('speed up')
        highSpeed = True
        curDelay = max(1, curDelay-5 )
    elif key == ord('-'):
        print('speed down')
        highSpeed = True
        curDelay = min(1000, curDelay+5 )
    elif key == ord('r'):
        print('free run')
        highSpeed = False
        curDelay = 1
    elif key == ord('r'):
        print('free run')
        highSpeed = False
        curDelay = 1
    elif key == 81: #left
        print('left')
        index-=2
    else:
        print('key pressed ', key)

    index +=1


        
        # cv2.waitKey(0)

cv2.destroyAllWindows() 

# # split to train - 0.6, validation - 0.1, test - 0.3 sets
# df_train_set, df_test_set = train_test_split(df_pairs, test_size=0.3)
# df_train_set, df_validation_set = train_test_split(df_train_set, test_size=10 / 70)

# print('Dataset size: ', df_pairs.shape[0])
# print('Train set size: ', df_train_set.shape[0], f'({df_train_set.shape[0]/df_pairs.shape[0]:.0%})')
# print('Validation set size: ', df_validation_set.shape[0], f'({df_validation_set.shape[0]/df_pairs.shape[0]:.0%})')
# print('Test set size: ', df_test_set.shape[0], f'({df_test_set.shape[0]/df_pairs.shape[0]:.0%})')

# # saving csv files
# df_train_set.to_csv(os.path.join(main_path, 'train_set.csv'), header=False)
# df_validation_set.to_csv(os.path.join(main_path, 'validation_set.csv'), header=False)
# df_test_set.to_csv(os.path.join(main_path, 'test_set.csv'), header=False)






# flc_files = os.listdir(flc_path)
# flc_files_idx = [csv_name_list.index(element) for element in flc_files]
#
# fls2_files = natsorted(os.listdir(fls2_path))
# fls2_files_number = list(map(extract_digits, fls2_files))
# fls2_files_idx = [csv_name_list.index(element) for element in fls2_files_number]
#
# if len(fls2_files_idx) < len(flc_files_idx):
#     flag = 'camera'
#     small_relevant = fls2_files_idx
#     large_relevant = flc_files_idx
# else:
#     flag = 'not_camera'
#     small_relevant = flc_files_idx
#     large_relevant = fls2_files_idx
#
# pairs_large_idx = [find_closest_index(element, large_relevant) for element in small_relevant]
#
# if flag == 'camera':
#     fls_pair_files = fls2_files
#     flc_pair_files = list(map(csv_name_list.__getitem__, pairs_large_idx))
# else:
#     fls_pair_files = list(map(csv_name_list.__getitem__, pairs_large_idx))
#     flc_pair_files = flc_files_idx
#
# df = pd.DataFrame(data={'FLC': flc_pair_files, 'FLS': fls_pair_files})
# df['FLC'] = df['FLC'].apply(lambda a: os.path.join(flc_path, a))
# df['FLS'] = df['FLS'].apply(lambda a: os.path.join(fls2_path, a))

# dataset_size = df.shape[0]
# train_set_size = int(0.7 * dataset_size)
# test_set_size = dataset_size - train_set_size
#
# df_train_set, df_test_set = train_test_split(df, test_size=0.3)
#
# df_train_set.to_csv(os.path.join(main_path, 'train_set.csv'), header=False)
# df_test_set.to_csv(os.path.join(main_path, 'test_set.csv'), header=False)

# flc_relevant = [element for element in flc_files if element in csv_name_list]
# fls2_relevant = natsorted([element for element in fls2_files_number if element in csv_name_list])
#
# flc_fls2_relevant = [element for element in csv_name_list if element in flc_relevant + fls2_relevant]
# flc_fls2_bool = np.array(list(map(lambda a: find_type(a, flc_relevant), flc_fls2_relevant)))
# flc_fls2_bool_shift = np.roll(flc_fls2_bool, -1)
# sub = flc_fls2_bool - flc_fls2_bool_shift
#
# relevant_idx_flc = np.where(sub == 1)[0]
# relevant_idx_fls2 = relevant_idx_flc + 1
#
# flc_list = list(map(flc_fls2_relevant.__getitem__, relevant_idx_flc))
# fls2_list = list(map(flc_fls2_relevant.__getitem__, relevant_idx_fls2))
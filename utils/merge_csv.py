import os
import sys
import glob
import pandas as pd
# import utils.zmq_wrapper as utils
# from player import parse
import argparse

from datetime import datetime

usageDescription = 'parse all records'

parser = argparse.ArgumentParser(description='parse all records parser, %s'%usageDescription, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-i', '--folderPath', default=None, help=' path to records folder')



args = parser.parse_args()


# records_path = '/workspaces/RovVision2_old/bags/'
records_path = args.folderPath


all_records_directories = glob.glob(os.path.join(records_path, '*'))




# merge all CSVs to one
columns = ['topic', 'bagfile', 'filename', 'date', 'time', 'latitude', 'longitude', 'altitude', 'yaw', 'pitch', 'roll', 'velocity_x', 'velocity_y', 'velocity_z', 'depth']
df_msgs_info_all = pd.DataFrame(columns=columns)

for record in all_records_directories:
    print(record)
    if not os.path.isdir(record):
        print('not a folder - skipping')
        continue
    csv_file = os.path.join(record, 'image_nav_bagfile_name.csv')
    print(csv_file)

    try:
        table = pd.read_csv(csv_file)
    except FileNotFoundError:
        print('image_nav_bagfile_name not found in ', record)
        # continue
        break
    
    # print(table)
    if table.size == 0:
        continue



    table = table.iloc[1: , :]  # remove first row of headers




    df_msgs_info_all = df_msgs_info_all.append(table, ignore_index=True)
    

df_msgs_info_all.to_csv(os.path.join(records_path, 'df_msgs_info_all.csv'), index=False)




# python3 parse_recorded_data.py -r /docker/bags/20220531_111624   -t -f -q 
# parse()
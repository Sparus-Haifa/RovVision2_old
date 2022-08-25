import os
import sys
import glob
import pandas as pd
# import utils.zmq_wrapper as utils
# from player import parse


# recPath = '/docker/bags/20220531_111624'

# os.chdir("utils")

# args = ['', '-r', '/docker/bags/20220531_111624', '-t', '-f', '-q']


records_path = '/docker/bags/'

all_records_directories = glob.glob(os.path.join(records_path, '*'))


# for record in all_records_directories:

#     args = ['', '-r', record, '-t', '-f', '-q']

#     # sys.argv = [old_sys_argv[0]] + args
#     sys.argv = args

#     exec(open('player.py').read())



columns = ['topic', 'bagfile', 'label', 'date', 'time', 'latitude', 'longitude', 'altitude', 'yaw', 'pitch', 'roll', 'velocity_x', 'velocity_y', 'velocity_z', 'depth']
df_msgs_info_all = pd.DataFrame(columns=columns)

for record in all_records_directories:
    csv_file = os.path.join(record, 'image_nav_bagfile_name.csv')
    print(csv_file)
    table = pd.read_csv(csv_file)
    table = table.iloc[1: , :]  # remove first row of headers

    df_msgs_info_all = df_msgs_info_all.append(table, ignore_index=True)
    

df_msgs_info_all.to_csv(os.path.join(records_path, 'df_msgs_info_all.csv'), index=False)




# python3 parse_recorded_data.py -r /docker/bags/20220531_111624   -t -f -q 
# parse()
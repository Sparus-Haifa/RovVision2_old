import os
import sys
import glob
import pandas as pd
# import utils.zmq_wrapper as utils
# from player import parse

from datetime import datetime



# recPath = '/docker/bags/20220531_111624'

# os.chdir("utils")

# args = ['', '-r', '/docker/bags/20220531_111624', '-t', '-f', '-q']


records_path = '/docker/bags/'

all_records_directories = glob.glob(os.path.join(records_path, '*'))


# fix times:
start_date_time_str = '01/01/22 00:00:00:00'
custom_start_dateTime =  datetime.strptime(start_date_time_str, '%d/%m/%y %H:%M:%S:%f')


cur_timeStamp = None



x = 0
for record in all_records_directories:
    # break
    x+=1
    print(record)
    if not os.path.isdir(record):
        print('skipping')
        continue

    # -q showVideo
    args = ['', '-r', record, '-t', '-f', '-q', '-H']
    # args = ['', '-r', record, '-t', '-f', '-H']
    # args = ['', '-r', record, '-t', '-f']

    # sys.argv = [old_sys_argv[0]] + args
    sys.argv = args

    # exec(open('player copy 3.py').read())
    exec(open('player.py').read())
    
    # if x==3:
    #     break
    
    # exit()



columns = ['topic', 'bagfile', 'label', 'date', 'time', 'latitude', 'longitude', 'altitude', 'yaw', 'pitch', 'roll', 'velocity_x', 'velocity_y', 'velocity_z', 'depth']
df_msgs_info_all = pd.DataFrame(columns=columns)

for record in all_records_directories:
    print(record)
    if not os.path.isdir(record):
        print('skipping')
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
    # fix timings

    # for timeStamp in table['time']:

    first_data_row = table.iloc[1]
    startDate = first_data_row['date']
    startTime = first_data_row['time']

    # a = datetime(2017, 6, 21, 18, 25, 30)

    start_timeStamp = datetime.strptime(startDate + '_' + startTime, '%Y_%m_%d_%H_%M_%S_%f')
    # first_time = datetime.strptime(startDate, '%Y_%m_%d')
    

    # print(start_timeStamp)

    # print(f'{startDate}, {startTime}')

    # print(table.head)
    for index, row in table.iterrows():
        break
        cur_date, cur_time = row['date'], row['time']
        cur_timeStamp = datetime.strptime(cur_date + '_' + cur_time, '%Y_%m_%d_%H_%M_%S_%f')
        new_timeStamp = cur_timeStamp - start_timeStamp
        # start_timeStamp = cur_timeStamp

        # cur_date = datetime.strptime(new_timeStamp, '%Y_%m_%d').date()

        new_dateTime = custom_start_dateTime + new_timeStamp
        new_date = new_dateTime.strftime('%Y_%m_%d')
        new_time = new_dateTime.strftime('%H_%M_%S_%f')

        # row['date'], row['time'] = new_date, new_time
        table.loc[index, 'date'] = new_date
        table.loc[index, 'time'] = new_time


        # print(row['date'], row['time'], new_date, new_time)


    #     if index == 5:
    #         break

    # exit()

    if cur_timeStamp is not None:
        custom_start_dateTime = new_dateTime


    table = table.iloc[1: , :]  # remove first row of headers




    df_msgs_info_all = df_msgs_info_all.append(table, ignore_index=True)
    

df_msgs_info_all.to_csv(os.path.join(records_path, 'df_msgs_info_all.csv'), index=False)




# python3 parse_recorded_data.py -r /docker/bags/20220531_111624   -t -f -q 
# parse()
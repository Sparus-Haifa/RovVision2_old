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




# Create images and/or csv for every folder
for record in all_records_directories:
    # break
    print(record)
    if not os.path.isdir(record):
        print('skipping')
        continue

    # -q showVideo
    # args = ['', '-r', record, '-t', '-f', '-H']

    args = ['', '-r', record, '-t', '-f', '-q', '-H'] # no video
    # args = ['', '-r', record, '-f', '-q', '-H'] # parse only
    # args = ['', '-r', record, '-f', '-q', '-H']
    # args = ['', '-r', record, '-t', '-f', '-H']
    # args = ['', '-r', record, '-t', '-f']

    # sys.argv = [old_sys_argv[0]] + args
    sys.argv = args

    # exec(open('player copy 3.py').read())
    exec(open('utils/player.py').read())

    
    # exit()


import os
import pandas as pd
import numpy as np
import re
from natsort import natsorted
from sklearn.model_selection import train_test_split
from pathlib import Path
import cv2
import tkinter as tk
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
play_sections = False


if not main_path:
    print('ERROR: no path to csv')
    print('Usage: python findpairs.py -i [path_to_csv]')
    exit()

# Create the main window
window = tk.Tk()
window.title("Video Player")

# Create a canvas to display the video
canvas = tk.Canvas(window, width=640, height=480)
canvas.pack()

play_button = tk.Button(window, text="Play/Pause", command=lambda: print("play/pause"))
play_button.pack()


filename = os.path.basename(main_path)
main_path = os.path.dirname(main_path)

print('main_path', main_path)



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

print("opening", csv_path)

# data frame for the CSV
df = pd.read_csv(csv_path)

print("file loaded")


# open limits.csv
limits_df = pd.read_csv(os.path.join(main_path, 'sections.csv'))

# print(limits_df)
# exit()

# section of bagfile
section = 0

index = 0
# for index in
skip = True
# while 0 <= index < len(df): 
while True:
    row = df.iloc[index]
    index +=1
    # print(row['FLC'], row['FLS'])
    section_index, flc, fls, bagfile = (row['Index'], row['FLC'], row['FLS'], row['bagfile'])
    print("flc", flc)
    print("fls", fls)
    print("bagfile", bagfile)
    # flc_img = cv2.imread(flc)

    print("jumping to index")

    #get the limits for the current bagfile
    limits = limits_df.loc[limits_df['bagfile'] == bagfile]
    num_of_sections = len(limits)
    print(limits)
    print("num_of_sections", num_of_sections)
    print("section", section)
    # print("first section", limits['first_image'].iloc[section])
    # print("second section", limits['first_image'].iloc[section + 1])

    # if flc is less than the lower limit, jump to the lower limit
    print("section_index", section_index)
    print("limits['first_image'].iloc[section]", limits['first_image'].iloc[section])
    if play_sections and section_index < limits['first_image'].iloc[section]:
        print("section_index is less than the lower limit, jump to the lower limit")
        index = limits['first_image'].iloc[section]
        continue

    # if section_index is more than the upper limit, jump to the next bagfile if it exists or to the next section
    print("section_index", section_index)
    print("limits['last_image'].iloc[section]", limits['last_image'].iloc[section])
    if play_sections and section_index > limits['last_image'].iloc[section]:
        print("section_index is more than the upper limit, jump to the next bagfile or to the next section")
        # if there is another section, jump to it
        if section < num_of_sections - 1:
            print("there is another section, jump to it")
            section += 1
            section_index = limits['first_image'].iloc[section]
            index = df.loc[(df['bagfile'] == bagfile) & (df['Index'] == section_index)].index[0]
            continue

        # find the next bagfile
        print("section_index is more than the upper limit, jump to the next bagfile if it exists")
        print("bagfile", bagfile)
        print("limits_df['bagfile']", limits_df['bagfile'])
        print("limits_df['bagfile'] > bagfile", limits_df['bagfile'] > bagfile)
        print("limits_df.loc[limits_df['bagfile'] > bagfile]['bagfile']", limits_df.loc[limits_df['bagfile'] > bagfile]['bagfile'])
        # get the 
        # next_bagfile = limits_df.loc[limits_df['bagfile'] > bagfile]['bagfile'].iloc[0]
        # Select the rows that contain the value 'a' in the 'col' column
        df_selected = limits_df[limits_df['bagfile'].isin([bagfile])]

        # Get the next value after 'a'
        next_bagfile = limits_df.loc[df_selected.index[-1] + 1, 'bagfile']
        print("next bagfile", next_bagfile)
        # exit()
        # set the index to the first image of the next bagfile from the df dataframe
        index = df.loc[(df['bagfile'] == next_bagfile) & (df['Index'] == limits_df.loc[limits_df['bagfile'] == next_bagfile]['first_image'].iloc[0])].index[0]
        print("index", index)
        section = 0
        # exit()
        continue





    # exit()

    flc_filename = f"{flc:08d}.tiff"
    fls_filename = f"{fls:08d}.tiff"

    print("opening image")
    print(main_path, bagfile, "imgs", flc)
    flc_path = os.path.join(main_path, bagfile, 'imgs', flc_filename)
    fls_path = os.path.join(main_path, bagfile, 'imgs', fls_filename)
    print(section_index, flc_path, fls_path, "of "+ str(len(df)))

    # if flc!="00032822.tiff" and skip:
    #     continue
    skip=False

    flc_img = cv2.imread(flc_path)

    text = f"{index}"
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Set the text color and thickness
    color = (255, 0, 0)  # Red
    thickness = 2

    # Get the size of the text
    text_size = cv2.getTextSize(text, font, 1, thickness)[0]

    # Calculate the position of the text
    # text_x = (flc_img.shape[1] - text_size[0]) // 2
    # text_y = (flc_img.shape[0] + text_size[1]) // 2

    # Add the text to the image
    cv2.putText(flc_img, text, (10, 30), font, 1, color, thickness, cv2.LINE_AA)



    cv2.imshow('FLC', flc_img)

    fls_img = cv2.imread(fls_path)
    scale_percent = 200 # percent of original size
    width = int(fls_img.shape[1] * scale_percent / 100)
    height = int(fls_img.shape[0] * scale_percent / 100)
    dim = (width, height)
    fls_img = cv2.resize(fls_img, dim, interpolation=cv2.INTER_LINEAR)
    cv2.imshow('FLS', fls_img)


    # print("wait key")
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
        if play_sections:
            # if we back to the previous section, we need to skip the last image of the section according to the limits
            if df.iloc[index]['bagfile'] != bagfile:
                # if we back to the previous bagfile, we need to skip the last image of the bagfile according to the limits
                # select the bagfile, one above the current one
                bagfile = df.iloc[index]['bagfile']
                print("previous bagfile", bagfile)
                limits = limits_df.loc[limits_df['bagfile'] == bagfile]
                section = len(limits) - 1
                print(limits)
                section_index = limits['last_image'].iloc[section]
                print("section_index", section_index)
                # get index of the last image of the previous bagfile
                index = df.loc[(df['bagfile'] == bagfile) & (df['Index'] == section_index)].index[0]
                print("index",index)
                print("back to previous bagfile, skipping last image")
                continue


            print("section_index", section_index)
            print("limits['first_image'].iloc[section]", limits['first_image'].iloc[section])
            if section_index <= limits['first_image'].iloc[section]:
                print("section_index is less than the lower limit, jump to the lower limit")
                # select the section, one above the current one
                section = max(0, section - 1)
                print("previous section", section)
                section_index = limits['last_image'].iloc[section]
                print("section_index", section_index)
                # get index of the last image of the previous section
                index = df.loc[(df['bagfile'] == bagfile) & (df['Index'] == section_index)].index[0]
                print("index",index)
                print("back to previous section, skipping last image")
                continue



    elif key == ord("."):
        print("skip 100")
        index+=100
    elif key == ord(","):
        print("back 100")
        index-=100
    elif key == ord("s"):
        index-=1
        if play_sections:
            play_sections = False
            print("play all")
        else:
            play_sections = True
            print("play sections")
    # else:
    #     print('key pressed ', key)

    if index >= len(df):
        print("index is more than the length of the df, exiting")
        index = len(df) - 1


    if index < 0:
        print("index is less than 0")
        index = 0


        
        # cv2.waitKey(0)

cv2.destroyAllWindows() 
window.mainloop()
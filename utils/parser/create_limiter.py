import argparse
import os
import pandas as pd

usageDescription = 'finding pairs'

parser = argparse.ArgumentParser(description='find pairs parser, %s'%usageDescription, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-i', '--csvPath', default=None, help=' path to input csv file ')
args = parser.parse_args()

main_path = args.csvPath

if not main_path:
    print('ERROR: no path to csv')
    print('Usage: python findpairs.py -i [path_to_csv]')
    exit()


filename = os.path.basename(main_path)
main_path = os.path.dirname(main_path)

print('main_path', main_path)

csv_path = os.path.join(main_path, filename)

print("opening", csv_path)

# data frame for the CSV
df = pd.read_csv(csv_path)

print("file loaded")

# get unique bagfile names
bagfiles = df['bagfile'].unique()

print(bagfiles)

# create a new df where for every bagfile we have a row with the first and last image
new_df = pd.DataFrame(columns=['bagfile', 'first_image', 'last_image'])

for bagfile in bagfiles:
    # get all rows for this bagfile
    bagfile_df = df[df['bagfile'] == bagfile]

    # get the first and last image
    first_image = bagfile_df['FLC'].iloc[0]
    last_image = bagfile_df['FLC'].iloc[-1]

    # add a row to the new df
    new_df = new_df.append({'bagfile': bagfile, 'first_image': first_image, 'last_image': last_image}, ignore_index=True)
    # exit()

print(new_df)

# save the new df to a csv in main_path directory
new_df.to_csv(os.path.join(main_path, 'limits.csv'), header=True)

import argparse
import os
import pandas as pd

class SectionCreator:
    def __init__(self, main_path) -> None:
        self.main_path = main_path

        if not self.main_path:
            print('ERROR: no path to csv')
            print('Usage: python3 create_sections.py -i [path_to_csv]')
            exit()

        self.filename = os.path.basename(self.main_path)
        self.main_path = os.path.dirname(self.main_path)

        print('main_path', self.main_path)

        self.csv_path = os.path.join(self.main_path, self.filename)

        print("opening", self.csv_path)

        # data frame for the CSV
        self.df = pd.read_csv(self.csv_path)

        print("file loaded")

        # get unique bagfile names
        self.bagfiles = self.df['bagfile'].unique()

        print(self.bagfiles)

        # create a new df where for every bagfile we have a row with the first and last image
        self.new_df = pd.DataFrame(columns=['bagfile', 'first_image', 'last_image'])

    def create_sections(self):
        for bagfile in self.bagfiles:
            # get all rows for this bagfile
            bagfile_df = self.df[self.df['bagfile'] == bagfile]

            # get the first and last image
            first_image = bagfile_df['Index'].iloc[0]
            last_image = bagfile_df['Index'].iloc[-1]

            # add a row to the new df
            self.new_df = self.new_df.append({'bagfile': bagfile, 'first_image': first_image, 'last_image': last_image}, ignore_index=True)
            # exit()

        print(self.new_df)

        # save the new df to a csv in main_path directory
        self.new_df.to_csv(os.path.join(self.main_path, 'sections.csv'), header=True)

if __name__ == '__main__':
    usageDescription = 'creating sections'
    
    parser = argparse.ArgumentParser(description='creating sections, %s'%usageDescription, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-i', '--csvPath', default=None, help=' path to input csv file ')
    args = parser.parse_args()

    main_path = args.csvPath

    section_creator = SectionCreator(main_path)
    section_creator.create_sections()



# usageDescription = 'finding pairs'

# parser = argparse.ArgumentParser(description='find pairs parser, %s'%usageDescription, formatter_class=argparse.RawTextHelpFormatter)
# parser.add_argument('-i', '--csvPath', default=None, help=' path to input csv file ')
# args = parser.parse_args()

# main_path = args.csvPath

# if not main_path:
#     print('ERROR: no path to csv')
#     print('Usage: python findpairs.py -i [path_to_csv]')
#     exit()


# filename = os.path.basename(main_path)
# main_path = os.path.dirname(main_path)

# print('main_path', main_path)

# csv_path = os.path.join(main_path, filename)

# print("opening", csv_path)

# # data frame for the CSV
# df = pd.read_csv(csv_path)

# print("file loaded")

# # get unique bagfile names
# bagfiles = df['bagfile'].unique()

# print(bagfiles)

# # create a new df where for every bagfile we have a row with the first and last image
# new_df = pd.DataFrame(columns=['bagfile', 'first_image', 'last_image'])

# for bagfile in bagfiles:
#     # get all rows for this bagfile
#     bagfile_df = df[df['bagfile'] == bagfile]

#     # get the first and last image
#     first_image = bagfile_df['FLC'].iloc[0]
#     last_image = bagfile_df['FLC'].iloc[-1]

#     # add a row to the new df
#     new_df = new_df.append({'bagfile': bagfile, 'first_image': first_image, 'last_image': last_image}, ignore_index=True)
#     # exit()

# print(new_df)

# # save the new df to a csv in main_path directory
# new_df.to_csv(os.path.join(main_path, 'sections.csv'), header=True)

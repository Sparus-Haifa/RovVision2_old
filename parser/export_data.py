
import os
import glob
import argparse
import pandas as pd
from player import Player
from find_pairs import PairFinder
from split_pairs import PairSplitter


class Exporter:
    def __init__(self, recPath, showVideo, freeRun, saveTiff, saveAvi, saveMetadata) -> None:
        self.recPath = recPath
        self.showVideo = showVideo
        self.freeRun = freeRun
        self.saveTiff = saveTiff
        self.saveAvi = saveAvi
        self.saveMetadata = saveMetadata
        self.all_records_directories = glob.glob(os.path.join(self.recPath, '*'))


    def run_player(self):

        # Create images and/or csv for every folder
        for record in self.all_records_directories:
            print(record)
            # if "20221213_102542" not in record:
            #     continue

            if not os.path.isdir(record): # skip files. process only directories
                print('skipping')
                continue


            player = Player(recPath=record, skipFrame=-1, saveTiff=self.saveTiff, showVideo=self.showVideo, freeRun=self.freeRun, highQuality=False, saveAvi=self.saveAvi, generateDataFrame=self.saveMetadata)
            player.parse()

    def merge_csv(self):
        # merge all CSVs to one
        columns = ['topic', 'bagfile', 'value', 'date', 'time']
        df_msgs_info_all = pd.DataFrame(columns=columns)

        for record in self.all_records_directories:
            print(record)
            if not os.path.isdir(record):
                print('not a folder - skipping')
                continue
            csv_file = os.path.join(record, 'data.csv')
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
            

        df_msgs_info_all.to_csv(os.path.join(self.recPath, 'data.csv'), index=False)

    def find_pairs(self):
        pair_finder = PairFinder(main_path=os.path.join(self.recPath, 'data.csv'), save_pairs=True)
        pair_finder.find()

    def split_pairs(self):
        pair_splitter = PairSplitter(csv_file=os.path.join(self.recPath, 'pairs.csv'))
        pair_splitter.split_pairs()



def main():
    usageDescription = 'export data'

    # parser = argparse.ArgumentParser(description='synced record parser, %s'%usageDescription, formatter_class=argparse.RawTextHelpFormatter)
    # parser.add_argument('recPath', help=' path to record ')
    # parser.add_argument('-t', '--saveTiff', action='store_true', help='save tiffs files to record folder')
    # parser.add_argument('-q', '--showVideo', action='store_false', help='quite run, if -q - parse only, no show')
    # parser.add_argument('-f', '--freeRun', action='store_true', help='Not true realtime run')
    # # parser.add_argument('-H', '--highQuality', action='store_true', help='Parse also high quality')
    # parser.add_argument('-V', '--saveAvi', action='store_true', help='quite run, if -V - create avi files')
    # parser.add_argument('-d', '--saveMetadata', action='store_true', help='save a csv file with metadata')

    

    # args = parser.parse_args()

    # exporter = Exporter(recPath=args.recPath, showVideo=args.showVideo,  freeRun=args.freeRun, saveTiff=args.saveTiff, saveAvi=args.saveAvi, saveMetadata=args.saveMetadata)

    recPath = "/workspaces/RovVision2_Sonar/bags"
    showVideo = False
    freeRun = True
    saveTiffs = True
    saveAvi = False
    saveMeta = True

    exporter = Exporter(recPath=recPath, showVideo=showVideo,  freeRun=freeRun, saveTiff=saveTiffs, saveAvi=saveAvi, saveMetadata=saveMeta)


    #export images and metadata.csv
    
    exporter.run_player()

    exporter.merge_csv()

    exporter.find_pairs()

    # exporter.split_pairs()


 

    



if __name__=="__main__":
    main()
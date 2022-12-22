import pandas as pd
import cv2
import numpy as np
import glob
import os
from datetime import datetime, timedelta




class VideoMaker():
    def __init__(self, csv_path, topic_of_intrest):
        self.csv_path = csv_path
        self.folder_path = os.path.dirname(csv_path)
        self.topic_of_intrest = topic_of_intrest
        self.output_file = os.path.join(self.folder_path, f'{self.topic_of_intrest[2:-1]}.avi')
        self.curr_image_path = None
        self.last_image_path = None
        self.last_timestamp = None

    def run(self):

        df = pd.read_csv(self.csv_path)

        sample_image_path = df.loc[df["topic"] == self.topic_of_intrest].iloc[0]['label']
        img = cv2.imread(sample_image_path)
        height, width, channels = img.shape
        frameSize = (width, height)
        # frameSize = (height, width)


        print('resolution', frameSize)
        print(f'saveing to {self.output_file}')

        # exit()

        fps = 10
        mpf = int((1/fps)*1000) # miliseconds per frame


        out = cv2.VideoWriter(self.output_file,cv2.VideoWriter_fourcc(*'DIVX'), fps, frameSize)




        for index, row in df.iterrows():
            topic = row['topic']
            t_day = row['date']
            t_time = row['time']
            self.curr_image_path = row['label']
            timestamp = datetime.strptime(t_day + '_' + t_time,"%Y_%m_%d_%H_%M_%S_%f")
            # print(topic, timestamp, path)

            if topic == self.topic_of_intrest:
                if not self.last_timestamp:
                    self.last_timestamp = timestamp
                    self.last_image_path = self.curr_image_path
                    print('frame')
                    img = cv2.imread(self.curr_image_path)
                    out.write(img)
                    continue

                # print(self.curr_image_path, self.last_image_path)
                if self.curr_image_path != self.last_image_path: # new frame
                    # print('next', timestamp, self.last_timestamp)
                    img = cv2.imread(self.curr_image_path)
                    print(img.shape)
                    while timestamp > self.last_timestamp:
                        # print('frame', timestamp)
                        self.last_timestamp = self.last_timestamp + timedelta(milliseconds=mpf)
                        out.write(img)
                    # print('image', self.curr_image_path)
                    self.last_timestamp = timestamp
                    self.last_image_path = self.curr_image_path



        img = cv2.imread(self.curr_image_path)
        out.write(img)


        out.release()
        print('done')


def main():

    csv_path = '/docker/bags/20220531_103744/image_nav_bagfile_name.csv'
    # topic_of_intrest = "b'topic_stereo_camera'"
    topic_of_intrest = "b'topic_sonar'"
    maker = VideoMaker(csv_path=csv_path, topic_of_intrest=topic_of_intrest)
    maker.run()



    



if __name__=='__main__':
    main()
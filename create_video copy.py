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
        self.topic_camera = "b'topic_stereo_camera'"
        self.topic_sonar = "b'topic_sonar'"
        self.curr_image_path = None
        self.last_image_path = None
        self.last_timestamp = None
        self.df = pd.read_csv(self.csv_path)
        self.fps = 10
        self.mpf = int((1/fps)*1000) # miliseconds per frame

        def setup_outputs(topic):
            # get image resolution
            sample_image_path = df.loc[df["topic"] == self.topic_of_intrest].iloc[0]['label']
            img = cv2.imread(sample_image_path)
            height, width, channels = img.shape
            frameSize = (width, height)
            # setup output filename
            output_file = os.path.join(self.folder_path, f'{topic[2:-1]}.avi')
            return cv2.VideoWriter(self.output_file,cv2.VideoWriter_fourcc(*'DIVX'), self.fps, frameSize)

        self.out_camera = setup_outputs(topic=self.topic_camera)
        self.out_sonar = setup_outputs(topic=self.topic_sonar)




    def run(self):

        


        # frameSize = (height, width)


        # print('resolution', frameSize)
        # print(f'saveing to {self.output_file}')

        # exit()




        # out = cv2.VideoWriter(self.output_file,cv2.VideoWriter_fourcc(*'DIVX'), fps, frameSize)




        for index, row in df.iterrows():
            topic = row['topic']
            t_day = row['date']
            t_time = row['time']
            self.curr_image_path = row['label']
            timestamp = datetime.strptime(t_day + '_' + t_time,"%Y_%m_%d_%H_%M_%S_%f")
            # print(topic, timestamp, path)

            if topic == self.topic_camera:
                if not self.last_timestamp:
                    self.last_timestamp = timestamp
                    self.last_image_path = self.curr_image_path
                    print('frame')
                    img = cv2.imread(self.curr_image_path)
                    self.out_camera.write(img)
                    continue

                # print(self.curr_image_path, self.last_image_path)
                if self.curr_image_path != self.last_image_path: # new frame
                    # print('next', timestamp, self.last_timestamp)
                    img = cv2.imread(self.curr_image_path)
                    while timestamp > self.last_timestamp:
                        # print('frame', timestamp)
                        self.last_timestamp = self.last_timestamp + timedelta(milliseconds=mpf)
                        self.out_camera.write(img)
                    # print('image', self.curr_image_path)
                    self.last_timestamp = timestamp
                    self.last_image_path = self.curr_image_path



        img = cv2.imread(self.curr_image_path)
        self.out_camera.write(img)


        self.out_camera.release()
        print('done')


def main():

    csv_path = '/docker/bags/20220531_103744/image_nav_bagfile_name.csv'

    maker = VideoMaker(csv_path=csv_path)
    maker.run()



    



if __name__=='__main__':
    main()
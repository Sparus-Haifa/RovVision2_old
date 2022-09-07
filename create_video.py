import pandas as pd
import cv2
import numpy as np
import glob
import os
from datetime import datetime, timedelta



class Topic():
    def __init__(self, name, label):
        self.name = name
        self.label = label
        self.size = None

class VideoMaker():
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.folder_path = os.path.dirname(csv_path)
        self.topics = {'camera': Topic('camera',"b'topic_stereo_camera'"), 'sonar': Topic('sonar', "b'topic_sonar'")}
        self.curr_image_path = {'camera': None, 'sonar': None}
        self.last_image_path = {'camera': None, 'sonar': None}
        self.last_timestamp = {'camera': None, 'sonar': None}
        self.first_frame_timestamp = None
        self.df = pd.read_csv(self.csv_path)
        self.fps = 10
        self.mpf = int((1/self.fps)*1000) # miliseconds per frame

        def setup_outputs(topic, topic_str):
            # get image resolution
            print(topic, topic_str)
            sample_image_path = self.df.loc[self.df["topic"] == topic_str].iloc[0]['label']
            img = cv2.imread(sample_image_path)
            height, width, channels = img.shape
            frameSize = (width, height)
            self.topics[topic].size = frameSize
            # setup output filename
            output_file = os.path.join(self.folder_path, f'{topic}.avi')
            return cv2.VideoWriter(output_file,cv2.VideoWriter_fourcc(*'DIVX'), self.fps, self.topics[topic].size)

        self.out = dict()
        for topic in self.topics.values():
            self.out[topic.name] = setup_outputs(topic.name, topic.label)




    def run(self):
        for index, row in self.df.iterrows():
            # fix topic names
            curr_topic = row['topic']
            for topic in self.topics.values():
                if topic.label == curr_topic:
                    curr_topic = topic.name

            t_day = row['date']
            t_time = row['time']
            self.curr_image_path[curr_topic] = row['label']
            timestamp = datetime.strptime(t_day + '_' + t_time,"%Y_%m_%d_%H_%M_%S_%f")
            # print(topic, timestamp, path)

            def process(topic):
                for topic in self.topics.values():
                    if topic.name == curr_topic:
                        # if not self.last_timestamp[topic.name]: # first frame of topic
                        #     self.last_timestamp[topic.name] = timestamp
                        #     if not self.first_frame_timestamp: # first frame of video:
                        #         self.first_frame_timestamp = timestamp

                            # self.last_image_path[topic] = self.curr_image_path[topic]
                            # print('frame')
                            # img = cv2.imread(self.curr_image_path[topic])
                            # self.out[topic].write(img)
                            # return

                        # print(self.curr_image_path, self.last_image_path)
                        first_frame_in_topic = self.last_image_path[topic.name] is None # first frame of topic
                        first_frame_in_video = self.first_frame_timestamp is None # first frame of video
                        frame_changed = self.curr_image_path[topic.name] != self.last_image_path[topic.name]
                        
                        if first_frame_in_topic and not first_frame_in_video:
                            img = np.zeros((topic.size[0],topic.size[1],3), np.uint8) # black image
                            self.last_timestamp[topic.name] = self.first_frame_timestamp
                            print('black image', topic.name)
                            black = True
                        else:
                            if first_frame_in_video:
                                 self.first_frame_timestamp = timestamp # update first frame of video
                            img = cv2.imread(self.curr_image_path[topic.name])
                        
                        



                            
                        if frame_changed and not first_frame_in_video:
                            while timestamp > self.last_timestamp[topic.name]:
                                # print('frame', timestamp)
                                self.last_timestamp[topic.name] = self.last_timestamp[topic.name] + timedelta(milliseconds=self.mpf)
                                self.out[topic.name].write(img)
                        print('image', self.curr_image_path[topic.name])
                        self.last_image_path[topic.name] = self.curr_image_path[topic.name] 
                        self.last_timestamp[topic.name] = timestamp # update first frame of topic
            
            process(curr_topic)



        # last frame
        for topic in self.topics.values():
            img = cv2.imread(self.curr_image_path[topic.name])
            self.out[topic.name].write(img)
            self.out[topic.name].release()
        


        print('done')


def main():

    csv_path = '/docker/bags/20220531_103744/image_nav_bagfile_name.csv'

    maker = VideoMaker(csv_path=csv_path)
    maker.run()



    



if __name__=='__main__':
    main()
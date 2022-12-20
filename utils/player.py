import os
import cv2
import sys
import glob
import numpy as np
import argparse
import time
import sys
sys.path.append('../')
sys.path.append('utils')
# print(sys.path)

import zmq_wrapper as utils
import zmq
import zmq_topics
import pickle

import pandas as pd
from datetime import datetime

usageDescription = 'usage while playing: \n\t(-) press space to run frame by frame \n\t(-) press r ro run naturally, ~10Hz \n\t(-) press +/- to increase/decrease playing speed'

parser = argparse.ArgumentParser(description='synced record parser, %s'%usageDescription, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-r', '--recPath', default=None, help=' path to record ')
parser.add_argument('-s', '--skipFrame', type=int, default=-1, help='start of parsed frame, by frame counter not file index')
parser.add_argument('-t', '--saveTiff', action='store_true', help='save tiffs files to record folder')
parser.add_argument('-q', '--showVideo', action='store_false', help='quite run, if -q - parse only, no show')
parser.add_argument('-f', '--freeRun', action='store_true', help='Not true realtime run')
parser.add_argument('-H', '--highQuality', action='store_true', help='Parse also high quality')
parser.add_argument('-V', '--saveAvi', action='store_true', help='quite run, if -V - create avi files')
parser.add_argument('-c', '--zeroClock', action=None, help='reset the clock to argument time')


args = parser.parse_args()



class Player:
    def __init__(self, recPath, skipFrame, saveTiff, showVideo, freeRun, highQuality, saveAvi, generateDataFrame):



        # import recorder 
        self.topicsList = [ [zmq_topics.topic_thrusters_comand,   zmq_topics.topic_thrusters_comand_port],
                    [zmq_topics.topic_lights,             zmq_topics.topic_controller_port],
                    [zmq_topics.topic_focus,              zmq_topics.topic_controller_port],
                    [zmq_topics.topic_depth,              zmq_topics.topic_depth_port],
                    [zmq_topics.topic_volt,               zmq_topics.topic_volt_port],
                    [zmq_topics.topic_imu,                zmq_topics.topic_imu_port],
                    [zmq_topics.topic_stereo_camera,      zmq_topics.topic_camera_port],
                    [zmq_topics.topic_system_state,       zmq_topics.topic_controller_port],
                    [zmq_topics.topic_att_hold_roll_pid,  zmq_topics.topic_att_hold_port],
                    [zmq_topics.topic_att_hold_pitch_pid, zmq_topics.topic_att_hold_port],
                    [zmq_topics.topic_att_hold_yaw_pid,   zmq_topics.topic_att_hold_port],
                    [zmq_topics.topic_depth_hold_pid,     zmq_topics.topic_depth_hold_port],
                    [zmq_topics.topic_motors_output,      zmq_topics.topic_motors_output_port],
                    [zmq_topics.topic_sonar,              zmq_topics.topic_sonar_port],
                ]


        usageDescription = 'usage while playing: \n\t(-) press space to run frame by frame \n\t(-) press r ro run naturally, ~10Hz \n\t(-) press +/- to increase/decrease playing speed'


        self.highQuality = highQuality
        self.recPath = recPath
        self.skipFrame = skipFrame 
        self.saveTiff = saveTiff
        self.showVideo = showVideo
        self.saveAvi = saveAvi
        self.highSpeed = freeRun
        self.generateDataFrame = generateDataFrame
        print('self.highSpeed', self.highSpeed)
        print('self.highQuality', self.highQuality)
        print('self.recPath', self.recPath)
        print('self.skipFrame', self.skipFrame)
        print('self.saveTiff', self.saveTiff)
        print('self.showVideo', self.showVideo)
        print('self.saveAvi', self.saveAvi)




        # datetime.strptime(date_time_str, '%d/%m/%y %H:%M:%S')
        # if self.showVideo:
        #     print(f"{self.showVideo}")
        #     exit()





        # dataframe variables
        self.columns = ['topic', 'bagfile', 'filename', 'date', 'time', 'latitude', 'longitude', 'altitude', 'yaw', 'pitch', 'roll', 'velocity_x', 'velocity_y', 'velocity_z', 'depth']
        self.df_msgs_info_cur_bag = pd.DataFrame(columns=self.columns)
        if self.showVideo:
            print('bla')
            self.winName = 'player_camera'
            self.winName_sonar = 'player_sonar'
            self.winNameLowRes = 'player - low Res'
            self.winNameLowResSonar = 'player - low Res - sonar'
            # cv2.namedWindow(winNameLowRes, 0)
            #cv2.setMouseCallback(winName, CallBackFunc)


        self.frameId = 0
        if self.highSpeed:
            self.curDelay = 1
        else:
            self.curDelay = 0

        ###
        self.font = cv2.FONT_HERSHEY_COMPLEX_SMALL
        self.org = (30, 30)
        self.fontScale = 2 #0.65
        self.color = (255, 255, 255)
        self.thickness = 2
        ##

        self.imgsPath = None
        self.writer = None
        self.writerLowRes = None


        # print(usageDescription)

        if self.recPath == None:
            print('no path provided')
            sys.exit(1)


    def create_data_frame(self, topic, bagfile, filename, date, time, latitude, longitude, altitude, yaw, pitch, roll, velocity_x, velocity_y, velocity_z, depth):
        # global df_msgs_info_cur_bag
        # print('create_data_frame')
        msg_info = {}
        msg_info['topic'] =  topic.decode('utf-8')
        msg_info['bagfile'] = bagfile
        msg_info['filename'] = filename
        msg_info['date'] = date
        msg_info['time'] = time
        
        nav_info = {}
        nav_info['latitude'] = latitude
        nav_info['longitude'] = longitude
        nav_info['altitude'] = altitude
        nav_info['yaw'] = yaw
        nav_info['pitch'] = pitch
        nav_info['roll'] = roll
        nav_info['velocity_x'] = velocity_x
        nav_info['velocity_y'] = velocity_y
        nav_info['velocity_z'] = velocity_z
        nav_info['depth'] = depth

        msg_df = pd.DataFrame(msg_info, index=[0])
        nav_df = pd.DataFrame(nav_info, index=[0])
        # df_msgs_info_cur_bag = df_msgs_info_cur_bag.append([msg_info, nav_info], ignore_index=True)
        new_row = pd.concat([msg_df, nav_df], axis=1, join="inner")
        self.df_msgs_info_cur_bag = self.df_msgs_info_cur_bag.append(new_row, ignore_index=True)


   


    def vidProc(self, curTopic, im, imLowRes, timestamp):
        # global curDelay, highSpeed, imgsPath, writer, writerLowRes

        # print(im[:20])
        # print(im.shape)
        # print(im.dtype)

        curImName = '%08d.tiff'%self.frameId

        if self.saveTiff: # create imgs folder
            if self.imgsPath is None:
                self.imgsPath = os.path.join(self.recPath, 'imgs')
                if not os.path.exists(self.imgsPath):
                    os.system('mkdir -p %s'%self.imgsPath)
        
        if self.showVideo:
            # print('showVideo')
            if curTopic == zmq_topics.topic_stereo_camera:
                winName_current = self.winName
            else:  # zmq_topics.topic_sonar
                winName_current = self.winName_sonar
            print(winName_current)
            cv2.namedWindow(winName_current, 0)

        if im is not None:
            # print('im not none')
            im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        
            showIm = np.copy(im)
        
            showIm = cv2.putText(showIm, '%04d '%(self.frameId), self.org, self.font,
                    self.fontScale, self.color, self.thickness, cv2.LINE_AA)

            # print("d1")

            if self.saveAvi and self.writer is None and im is not None:
                (h, w) = showIm.shape[:2]
                ### option for uncompressed raw
                #fourcc = cv2.VideoWriter_fourcc(*'DIB ')
                #fourcc = cv2.VideoWriter_fourcc(*'3IVD')
                fourcc = cv2.VideoWriter_fourcc(*'RGBA')
                #fourcc = cv2.VideoWriter_fourcc(*'DIVX')
                #import ipdb; ipdb.set_trace()
                vidFileName = os.path.join(self.recPath, 'out.avi')
                self.writer = cv2.VideoWriter(vidFileName, fourcc, 2,
                                                (w, h), True)
                self.writer.write(showIm)
            elif self.saveAvi and im is not None:
                self.writer.write(showIm)

        


            # print("d2")


            if self.saveTiff:
                # curImName = '%08d.tiff'%frameId
                #cv2.imwrite( os.path.join(imgsPath, curImName), im,  [cv2.IMWRITE_JPEG_QUALITY, 100] )
                # cv2.imwrite( os.path.join(imgsPath, curImName), im )
                cv2.imwrite( os.path.join(self.imgsPath, curImName), im )
                # print(im[:20])
                #curImName = '%08d.jpg'%frameId
                #cv2.imwrite( os.path.join(imgsPath, curImName), im,  [cv2.IMWRITE_JPEG_QUALITY, 100] )
                
            # print("d3")
            if self.showVideo:
                # print('showing')
                cv2.imshow(winName_current, showIm) #im[:200,:])
            
            # print("d4")
                

        if imLowRes is not None:
            imLowRes = cv2.cvtColor(imLowRes, cv2.COLOR_BGR2RGB)
            showImLow = np.copy(imLowRes)
            showImLow = cv2.putText(showImLow, '%04d '%(self.frameId), self.org, self.font,
                    self.fontScale/2, self.color, self.thickness, cv2.LINE_AA)

            # print("d5")
            

            if self.saveAvi and self.writerLowRes is None:
                (h, w) = showImLow.shape[:2]
                ### option for uncompressed raw
                #fourcc = cv2.VideoWriter_fourcc(*'DIB ')
                #fourcc = cv2.VideoWriter_fourcc(*'3IVD')
                fourcc = cv2.VideoWriter_fourcc(*'RGBA')
                #fourcc = cv2.VideoWriter_fourcc(*'DIVX')
                #import ipdb; ipdb.set_trace()
                vidFileName = os.path.join(self.recPath, 'outLowRes.avi')
                self.writerLowRes = cv2.VideoWriter(vidFileName, fourcc, 10,
                                                    (w, h), True)
                self.writerLowRes.write(showImLow)
            elif self.saveAvi:
                self.writerLowRes.write(showImLow)

            # print("d6")
            
                
            if self.showVideo:
                # if curTopic == self.zmq_topics.topic_stereo_camera:
                if curTopic == zmq_topics.topic_stereo_camera:
                    winName_current = self.winNameLowRes
                    # cv2.namedWindow(window_topic, 0)
                else:
                    winName_current = self.winNameLowResSonar
                    # cv2.namedWindow(window_topic, 0)
                # zmq_topics.topic_sonar
                cv2.imshow(winName_current, showImLow) #im[:200,:])

            if self.saveTiff:
                # curImName = '%08d.tiff'%frameId
                #cv2.imwrite( os.path.join(imgsPath, curImName), im,  [cv2.IMWRITE_JPEG_QUALITY, 100] )
                # cv2.imwrite( os.path.join(imgsPath, curImName), im )
                # print(self.imgsPath)
                image_path = os.path.join(self.imgsPath, curImName)
                # print(image_path)
                cv2.imwrite( image_path, imLowRes )
                # print(im[:20])
                #curImName = '%08d.jpg'%frameId
                #cv2.imwrite( os.path.join(imgsPath, curImName), im,  [cv2.IMWRITE_JPEG_QUALITY, 100] )
            
        # print("d7")


        

        if self.showVideo:

            
            # print("wait key")
            key = cv2.waitKey(self.curDelay)&0xff
            # key = cv2.waitKey(0)
            if key == ord('q'):
                return False
            elif key == ord(' '):
                self.curDelay = 0
            elif key == ord('+'):
                self.highSpeed = True
                self.curDelay = max(1, self.curDelay-5 )
            elif key == ord('-'):
                self.highSpeed = True
                self.curDelay = min(1000, self.curDelay+5 )
            elif key == ord('r'):
                self.highSpeed = False
                self.curDelay = 1
            # print("wait key done")
            
        else:
            pass 
            #print('current frame process %d'%frameId)

        # print("d8")

        # generateDataFrame = True
        # if self.saveTiff and generateDataFrame:
        if self.generateDataFrame:
            cur_date = datetime.fromtimestamp(timestamp).strftime("%Y_%m_%d")
            cur_time = datetime.fromtimestamp(timestamp).strftime("%H_%M_%S_%f")
            data_frame = self.create_data_frame(topic=curTopic, 
                bagfile=os.path.basename(self.recPath), 
                filename=curImName, # os.path.join(self.recPath, 'imgs', curImName), 
                date=cur_date, time=cur_time,
                latitude=None, longitude=None, altitude=None, yaw=None, pitch=None, roll=None,
                velocity_x=None, velocity_y=None, velocity_z=None,
                depth=None
                )
            

        return True



    

    def parse(self):
        try:
            pubList = []
            topicPubDict = {}
            revTopicPubDict = {}
            for topic in self.topicsList:
                if topic[1] in pubList: # port already exist
                    print('reuse publisher port: %d %s'%(topic[1], topic[0]) )  
                    topicPubDict[topic[0]] = topicPubDict[revTopicPubDict[topic[1]]]
                else:
                    print('creats publisher on port: %d %s'%(topic[1], topic[0]) )
                    topicPubDict[topic[0]] = utils.publisher(topic[1])
                    revTopicPubDict[topic[1]] = topic[0]
                    pubList.append(topic[1])
            
            fpsTic = time.time()
            fpsCnt = 0.0
            
            if self.recPath is not None:
                self.vidPath = os.path.join(self.recPath, 'video.bin')
                self.sonPath = os.path.join(self.recPath, 'sonar.bin')
                self.vidQPath = os.path.join(self.recPath, 'videoQ.bin')
                self.sonQPath = os.path.join(self.recPath, 'sonarQ.bin')
                self.telemPath = os.path.join(self.recPath, 'telem.pkl')
                self.imgCnt = 0
                self.imRaw = None
                self.highResEndFlag = False
                self.lowResEndFlag = False
                self.telemRecEndFlag = False

                self.telFid  = None
                self.vidFid  = None
                self.vidQFid = None
                self.sonFid  = None
                self.sonQFid = None
                
                if os.path.exists(self.telemPath):
                    self.telFid = open(self.telemPath, 'rb')
                if os.path.exists(self.vidPath): # and highQuality:
                    self.vidFid = open(self.vidPath, 'rb')
                if os.path.exists(self.vidQPath):
                    self.vidQFid = open(self.vidQPath, 'rb')
                if os.path.exists(self.sonPath): # and highQuality:
                    self.sonFid = open(self.sonPath, 'rb')
                if os.path.exists(self.sonQPath):
                    self.sonQFid = open(self.sonQPath, 'rb')
                
                self.telId = 0
                # skip frame loop 
                while self.frameId < self.skipFrame:
                
                    curData = pickle.load(self.telFid)
                    self.telId += 1                
                    curTopic = curData[1][0]

                    if curTopic in [zmq_topics.topic_stereo_camera, zmq_topics.topic_sonar]:
                    # if curTopic == zmq_topics.topic_sonar:
                        file_ptr = sonFid
                        file_q_ptr = sonQFid                    
                        if curTopic == zmq_topics.topic_stereo_camera:
                            file_ptr = vidFid
                            file_q_ptr = vidQFid
                        self.frameId += 1
                        hasHighRes = curData[1][-1]
                        metaData = pickle.loads(curData[1][1])
                        imShape  = metaData[1]
                    
                        try:
                            imLowRes = np.fromfile(file_q_ptr, count=imShape[1]//2*imShape[0]//2*imShape[2], 
                                            dtype = 'uint8').reshape((imShape[0]//2, imShape[1]//2, imShape[2] ))

                            if hasHighRes:
                                imRaw = np.fromfile(file_ptr, count=imShape[1]*imShape[0]*imShape[2], dtype = 'uint8') #.reshape(imShape)
                        except:
                            pass
                else:
                    curData = pickle.load(self.telFid)
                nextData = pickle.load(self.telFid)
                nextTicToc = 0.9*(nextData[0] - curData[0]) 

                #import ipdb; ipdb.set_trace()
                
                while True:
                    
                    time.sleep(0.0001)
                    try:
                        data = curData #pickle.load(telFid)
                        self.telId += 1
                    except:
                        if not telemRecEndFlag:
                            print('record Ended...')
                            telemRecEndFlag = True
                            break
                        

                    curTopic = data[1][0]
                    # print(curTopic)
                    # if curTopic == zmq_topics.topic_sonar:
                    #     break
                    if curTopic in [zmq_topics.topic_stereo_camera, zmq_topics.topic_sonar]:
                        # print(curTopic)
                        # print('img')
                        file_ptr = self.sonFid
                        file_q_ptr = self.sonQFid                    
                        if curTopic == zmq_topics.topic_stereo_camera:
                            file_ptr = self.vidFid
                            file_q_ptr = self.vidQFid
                            
                        self.frameId += 1
                        hasHighRes = curData[1][-1]
                        metaData = pickle.loads(curData[1][1])
                        #print(self.frameId, metaData)
                        #pirint('-->', telData)
                        try:
                            if 'focus' in telData.keys():
                                print(self.frameId, telData['focus'])
                        except:
                            pass
                        fpsCnt+=1
                        if time.time() - fpsTic >= 5:
                            fps = fpsCnt/(time.time() - fpsTic)
                            print('player video fps %0.2f'%fps)
                            fpsCnt = 0.0
                            fpsTic = time.time()
                            
                        # frameId += 1
                        ## handle image
                        metaData = pickle.loads(data[1][1])
                        hasHighRes = data[1][-1]
                        
                        imShape  = metaData[1]
                        self.imgCnt  += 1
                        # load image
                        # print('lowResEndFlag', lowResEndFlag)
                        if not self.lowResEndFlag:
                            # print('trying low res', curTopic, imShape)
                            if True: # curTopic == zmq_topics.topic_stereo_camera:
                                try:
                                    imLowRes = np.fromfile(file_q_ptr, count=(imShape[1]//2)*(imShape[0]//2)*imShape[2], 
                                                        dtype = 'uint8').reshape((imShape[0]//2, imShape[1]//2, imShape[2] ))
                                except Exception as e:
                                    print(e)
                                    imLowRes = None
                                    if not lowResEndFlag:
                                        print('low res video ended')
                                        lowResEndFlag = True
                                        self.showVideo = False
                                        continue
                            if hasHighRes: # and curTopic != zmq_topics.topic_stereo_camera:
                                try:
                                    # print('trying high res', curTopic, imShape)
                                    imRaw = np.fromfile(file_ptr, count=imShape[1]*imShape[0]*imShape[2], dtype = 'uint8').reshape(imShape)
                                    # print('success')
                                except Exception as e:
                                    print('high res failed for topic', curTopic )
                                    print(e)
                                    imRaw = None
                                    if not highResEndFlag:
                                        print('high res video ended')
                                        highResEndFlag = True
                                        continue
                            else:
                                imRaw = None
                            # print('before')
                            timestamp = curData[0]
                            ret = self.vidProc(curTopic, imRaw, imLowRes, timestamp)
                            # print('done')
                            if not ret:
                                break
        
                            #import ipdb; ipdb.set_trace()
                            try:
                                if 'expVal' in metaData[3].keys():
                                    expVal = metaData[3]['expVal']
                                else:
                                    expVal = -1
                            except:
                                expVal = metaData[3].value
                                
                            # videoMsg = [zmq_topics.topic_sonar,
                            videoMsg = [zmq_topics.topic_stereo_camera,
                                                pickle.dumps((metaData[0], imLowRes.shape, expVal, metaData[2])),
                                                    imLowRes.tobytes()] # [topic, (frameId, frameShape, ts) rawFrame]
                            if curTopic == zmq_topics.topic_sonar:
                                videoMsg[0]=zmq_topics.topic_sonar
                            #print('-->', curTopic)
                            topicPubDict[curTopic].send_multipart(videoMsg)
                            
                    else:
                        #recTs = data[0]
                        # if curTopic != zmq_topics.topic_sonar:
                        telData = pickle.loads(data[1][1])
                        # print('sending...')
                        topicPubDict[curTopic].send_multipart([curTopic, pickle.dumps(telData)] )
                        
                        #pass
                        #topicPubDict[curTopic].send_multipart(data[1])
                
                    curData = nextData
                    nextData = pickle.load(self.telFid)
                        
                    if not self.highSpeed:
                        time.sleep(nextTicToc)
                        nextTicToc = 0.6*(nextData[0] - curData[0])
                        ### workaround - overcome a problem of serialization of telemetry
                        # next step is calculated by the telemtry time stamp - which can 
                        #recorded not in the right order, the player should be run initially by the recorder ts
                        ###
                        if nextTicToc<0:
                            nextTicToc = 0
                            print('--err--> next sleep err: %.5f'%(nextData[0]-curData[0] ) )
                        ###############################################################
                        
        except:
            import traceback
            traceback.print_exc()
        finally:
            print("--->",self.frameId, self.telId)
            if self.writer is not None:
                self.writer.release()
            if self.writerLowRes is not None:
                self.writerLowRes.release()
                # saving csv information in the bag file directory
            if self.generateDataFrame:
                csv_path = os.path.join(self.recPath, 'data.csv')
                print('Saving bag file information into CSV...')
                print(csv_path)
                self.df_msgs_info_cur_bag.to_csv(csv_path, index=False)
            print("done...")            
            



    '''
    cv2.namedWindow('low', 0)
    cv2.namedWindow('high', 0)
    '''
if __name__=='__main__':
    usageDescription = 'usage while playing: \n\t(-) press space to run frame by frame \n\t(-) press r ro run naturally, ~10Hz \n\t(-) press +/- to increase/decrease playing speed'

    parser = argparse.ArgumentParser(description='synced record parser, %s'%usageDescription, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-r', '--recPath', default=None, help=' path to record ')
    parser.add_argument('-s', '--skipFrame', type=int, default=-1, help='start of parsed frame, by frame counter not file index')
    parser.add_argument('-t', '--saveTiff', action='store_true', help='save tiffs files to record folder')
    parser.add_argument('-q', '--showVideo', action='store_false', help='quite run, if -q - parse only, no show')
    parser.add_argument('-f', '--freeRun', action='store_true', help='Not true realtime run')
    parser.add_argument('-H', '--highQuality', action='store_true', help='Parse also high quality')
    parser.add_argument('-V', '--saveAvi', action='store_true', help='quite run, if -V - create avi files')

    args = parser.parse_args()

    self.highQuality = args.highQuality
    self.recPath = args.recPath
    self.skipFrame = args.skipFrame 
    self.saveTiff = args.saveTiff
    self.showVideo = args.showVideo
    self.saveAvi = args.saveAvi
    self.highSpeed = args.freeRun
    print('self.highSpeed', self.highSpeed)


    print('self.highQuality', self.highQuality)
    print('self.recPath', self.recPath)
    print('self.skipFrame', self.skipFrame)
    print('self.saveTiff', self.saveTiff)
    print('self.showVideo', self.showVideo)
    print('self.saveAvi', self.saveAvi)
    print('self.highSpeed', self.highSpeed)
    player = Player(recPath=args.recPath, skipFrame=args.skipFrame, saveTiff=args.saveTiff, showVideo=args.showVideo, freeRun=args.freeRun, highQuality=args.highQuality, saveAvi=args.saveAvi)
    player.parse()

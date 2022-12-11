import os
import sys
import zmq
sys.path.append('idsCam/')
from camera import Camera
from pyueye import ueye
from utils import uEyeException
import cv2
import time

sys.path.append('../')
sys.path.append('../utils')

import zmq_topics
import zmq_wrapper as utils
import pickle
import traceback

socket_pub = utils.publisher(zmq_topics.topic_camera_port)
subSocks = [utils.subscribe([zmq_topics.topic_cam_toggle_auto_exp, 
                            zmq_topics.topic_cam_toggle_auto_gain,
                            zmq_topics.topic_cam_inc_exp,
                            zmq_topics.topic_cam_dec_exp,
                            zmq_topics.topic_cam_exp_val], zmq_topics.topic_cam_ctrl_port)]
class myCamera:
    def __init__(self):

        cam = Camera(device_id=0, buffer_count=3)
        self.cam = cam
        #======================================================================
        # Camera settings
        #======================================================================
        # TODO: Add more config properties (fps, gain, ...)
        self.cam.init()
        #cam.set_colormode(ueye.IS_CM_MONO8)
        cam.set_colormode(ueye.IS_CM_SENSOR_RAW8)
        #
        ret = cam.set_aoi(0, 0, 2048, 2048)
        cam.alloc()
        #cam.set_aoi(0, 0, 800, 800)
        print(f"INITIAL VALUES")
        print(f'fps: {cam.get_fps()}')
        print(f'Available fps range: {cam.get_fps_range()}')
        print(f'Pixelclock: {cam.get_pixelclock()}')
        #cam.set_pixelclock(30)

        cam.set_fps(5)
        print("")
        print(f"MODIFIED VALUES")
        print(f'fps: {cam.get_fps()}')
        print(f'Available fps range: {cam.get_fps_range()}')
        print(f'Pixelclock: {cam.get_pixelclock()}')



        self.gainCtl = 0
        self.expCtl = 1
        self.desExpVal = 50

        self.camStateFile = '../hw/camSate.pkl'

        self.camState = {}
        self.desExpVal = -1
        if os.path.exists(self.camStateFile):
            with open(self.camStateFile, 'rb') as fid:
                self.camState = pickle.load(fid)
                if 'aGain' in self.camState.keys():
                    self.gainCtl = self.camState['aGain']
                if 'aExp' in self.camState.keys():
                    self.expCtl = self.camState['aExp']
                if 'expVal' in self.camState.keys():
                    self.desExpVal = self.camState['expVal']


        if ('aExp' not in self.camState.keys() or self.camState['aExp'] == 0) and self.desExpVal > 0:
            newExp = cam.set_exposure(self.desExpVal)
            print('init exp value: ', newExp)
                    
                    
        self.camState['aGain'] = self.gainCtl
        self.camState['aExp'] = self.expCtl
        self.camState['expVal'] = self.desExpVal


        '''
        with open(camStateFile, 'wb') as fid:
            pickle.dump(self.camState, fid)
        '''

        cam.set_exposure_auto(self.expCtl)
        cam.set_gain_auto(self.gainCtl)

        curExp = cam.get_exposure()
        expJump = 0.3
        

    def run(self):
        tic = time.time()
        cnt = 0.0 
        frameCnt = 0

        while True:
            im0, ts = self.cam.capture_image() #, 110)

                
            if im0 is not None:
                cnt +=1
                frameCnt += 1
            
                imRaw = cv2.cvtColor(im0.astype('uint8'), cv2.COLOR_BAYER_BG2RGB)
                
                imShape = imRaw.shape
                
                QRes = cv2.resize(imRaw, (imShape[1]//2, imShape[0]//2))
                hasHighRes = True
                if frameCnt%4 == 0:
                    socket_pub.send_multipart([zmq_topics.topic_stereo_camera,
                    pickle.dumps((frameCnt, imShape, ts, self.camState, hasHighRes)), QRes.tobytes(),
                                                            imRaw.tobytes()])
                else:
                    hasHighRes = False
                    socket_pub.send_multipart([zmq_topics.topic_stereo_camera,
                                            pickle.dumps((frameCnt, imShape, ts, self.camState, hasHighRes)),
                                            QRes.tobytes(), b''])

                socket_pub.send_multipart( [zmq_topics.topic_stereo_camera_ts,
                                                        pickle.dumps( (frameCnt, ts) )] )
                
            socks=zmq.select(subSocks, [], [], 0.002)[0]
            for sock in socks:
                ret=sock.recv_multipart()
                topic,data=ret
                
                if topic==zmq_topics.topic_cam_toggle_auto_exp:
                    self.expCtl = pickle.loads(data)
                    print('set auto exp. to: %d'%self.expCtl)
                    self.cam.set_exposure_auto(self.expCtl)
                
                if topic==zmq_topics.topic_cam_toggle_auto_gain:
                    self.gainCtl = pickle.loads(data)
                    print('set auto gain to: %d'%self.gainCtl)
                    self.cam.set_gain_auto(self.gainCtl)
                
                if topic==zmq_topics.topic_cam_inc_exp:
                    self.curExp = self.cam.get_exposure()
                    newExp = self.curExp + self.expJump
                    print('set exp (inc) to: %.2f'%newExp)
                    newExp = self.cam.set_exposure(newExp)
                    print('--->', newExp)
                    self.self.camState['expVal'] = newExp
                    
                if topic==zmq_topics.topic_cam_dec_exp:
                    self.curExp = cam.get_exposure()
                    newExp = max(1, self.curExp - self.expJump )
                    print('set exp (dec) to: %.2f'%newExp)
                    newExp = self.cam.set_exposure(newExp)
                    print('--->', newExp)
                    self.self.camState['expVal'] = newExp
                    
                if topic == zmq_topics.topic_cam_exp_val:
                    self.curExp = self.cam.get_exposure()
                    newExp = pickle.loads(data)
                    print('set exp to: %.2f'%newExp)
                    newExp = self.cam.set_exposure(newExp)
                    print('--->', newExp)
                    self.camState['expVal'] = newExp
                    
                    

                self.camState['aGain'] = self.gainCtl
                self.camState['aExp'] = self.expCtl
                
                with open(self.camStateFile, 'wb') as fid:
                    pickle.dump(self.camState, fid)
                
                
            self.curExp = self.cam.get_exposure()
            self.camState['expVal'] = self.curExp
            
            if(time.time() - tic) > 3:
                fps = cnt/(time.time()-tic)
                print('current fps: %.2f currnet exp: %0.2f'%(fps, self.curExp) )
                cnt = 0.0
                tic = time.time()

def main():
    cam = myCamera()
    while True:
        try:
            cam.run()
        except KeyboardInterrupt:
            # quit
            sys.exit()
        except uEyeException as e:
            print('exception')
            print(e)
            traceback.print_exc()
            # continue
            cam.cam.exit()
            del cam
            cam = myCamera()
            # exit()

if __name__=='__main__':
    main()

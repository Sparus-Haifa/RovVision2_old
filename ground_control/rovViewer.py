#!/usr/bin/python3
# install ssh support - Exscript @ https://exscript.readthedocs.io/en/latest/install.html
# install matplotlib -  sudo apt-get install python3-matplotlib
# install tix - sudo apt-get install tix-dev


from tkinter import *
from tkinter import filedialog

#from idlelib.ToolTip import *

#from tkinter.tix import *
from PIL import Image, ImageTk
import io
import time
import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

import os
import sys
import socket
import pickle
import json

sys.path.append('../onboard')
sys.path.append('../utils')
sys.path.append('..')

import config
import zmq_topics
import zmq_wrapper as utils
from annotations import draw_mono, draw_sonar
import numpy as np
import cv2
from select import select
import zmq
import image_enc_dec

import argparse



#### matplotlib add
import matplotlib.pyplot as plt
####


parser = argparse.ArgumentParser(description='ROV viewer application', formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-r', '--rawVideo', action='store_true', help='Recieve raw video')
parser.add_argument('-s', '--sim', action='store_true', help='Simulation')
args = parser.parse_args()


'''
tm = time.gmtime()
filename = "logs/gui_{}_{}_{}__{}_{}_{}.log".format(
    tm.tm_year, tm.tm_mon, tm.tm_mday,
    tm.tm_hour, tm.tm_min, tm.tm_sec)
log_file = open(filename, "a")
'''

if args.sim:
    rovType = -1
    isSim = True 
else:
    rovType = int(os.environ.get('ROV_TYPE','1'))

print('--->', rovType)


class CycArr():
    def __init__(self,size=20000):
        self.buf=[]
        self.size=size

    def add(self,arr):
        self.buf.append(arr)
        if len(self.buf)>self.size:
            self.buf.pop(0)

    def get_data(self,labels):
        data = np.zeros((len(self.buf),len(labels)))
        for i,d in enumerate(self.buf):
            for j,l in enumerate(labels):
                if l in d:
                    data[i][j]=d[l]
                else:
                    data[i][j]=0
        return data

    def get_vec(self):
        return np.array([d for _,d in self.buf])

    def __len__(self):
        return len(self.buf)

    def reset(self):
        self.buf=[]


from threading import Thread

rovGuiCommandPublisher = utils.publisher(zmq_topics.topic_gui_port)

class rovDataHandler(Thread):
    def __init__(self, rovViewer):
        super().__init__()
        self.subs_socks=[]
        self.subs_socks.append(utils.subscribe([zmq_topics.topic_thrusters_comand,zmq_topics.topic_system_state],zmq_topics.topic_controller_port))
        self.subs_socks.append(utils.subscribe([zmq_topics.topic_button, zmq_topics.topic_hat], zmq_topics.topic_joy_port))
        self.subs_socks.append(utils.subscribe([zmq_topics.topic_imu], zmq_topics.topic_imu_port))
        self.subs_socks.append(utils.subscribe([zmq_topics.topic_depth], zmq_topics.topic_depth_port))
        self.subs_socks.append(utils.subscribe([zmq_topics.topic_depth_hold_pid], zmq_topics.topic_depth_hold_port))
        self.subs_socks.append(utils.subscribe([zmq_topics.topic_sonar], zmq_topics.topic_sonar_port))
        self.subs_socks.append(utils.subscribe([zmq_topics.topic_stereo_camera_ts], zmq_topics.topic_camera_port)) #for sync perposes
        self.subs_socks.append(utils.subscribe([zmq_topics.topic_tracker, zmq_topics.topic_tracker_result], zmq_topics.topic_tracker_port))
        self.subs_socks.append(utils.subscribe([zmq_topics.topic_volt], zmq_topics.topic_volt_port))
        self.subs_socks.append(utils.subscribe([zmq_topics.topic_hw_stats], zmq_topics.topic_hw_stats_port))
        
        self.subs_socks.append(utils.subscribe([zmq_topics.topic_motors_output], zmq_topics.topic_motors_output_port))
        
        self.subs_socks.append(utils.subscribe([zmq_topics.topic_pos_hold_pid_fmt%i for i in range(3)], zmq_topics.topic_pos_hold_port))
        self.subs_socks.append(utils.subscribe([zmq_topics.topic_att_hold_yaw_pid,
                                           zmq_topics.topic_att_hold_pitch_pid,
                                           zmq_topics.topic_att_hold_roll_pid], zmq_topics.topic_att_hold_port))
        
        self.rawVideo = args.rawVideo
        self.initImgSource()
        
        self.image = None 
        self.curFrameId = -1
        self.curExposure = -1


        # sonar
        self.initSonarImgSource()
        self.sonar_image = None 
        self.sonar_curFrameId = -1
        self.sonar_curExposure = -1       

        
        self.pubData = True
        self.socket_pub = None
        if self.pubData:
            self.socket_pub = utils.publisher(zmq_topics.topic_local_route_port,'0.0.0.0')
        self.rovViewer = rovViewer
        self.keepRunning = True
        self.telemtry = {}
        
    
    def initImgSource(self):
        if not self.rawVideo:
            self.imgSock =  socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP
            self.imgSock.bind(('', config.udpPort))
        else:
            self.subs_socks.append(utils.subscribe([zmq_topics.topic_stereo_camera], zmq_topics.topic_camera_port))

    def initSonarImgSource(self):
        if not self.rawVideo:
            self.sonar_imgSock =  socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP
            self.sonar_imgSock.bind(('', config.sonar_udpPort))
        else:
            self.subs_socks.append(utils.subscribe([zmq_topics.topic_sonar], zmq_topics.topic_sonar_port))
        
     
        
        
    def getNewImage(self):
        ret = [self.curFrameId, None]
        if self.image is not None:
            ret = [self.curFrameId, np.copy(self.image)]
            self.image = None
            #print("---image---", time.time())
        else:
            pass
            #print(time.time(), "no image")
            #print('--->', ret[0])
        return ret
    
    def getNewSonarImage(self):
        ret = [self.sonar_curFrameId, None]
        if self.sonar_image is not None:
            ret = [self.sonar_curFrameId, np.copy(self.sonar_image)]
            self.sonar_image = None
            #print("---image---", time.time())
        else:
            pass
            #print(time.time(), "no image")
            #print('--->', ret[0])
        return ret

    def getTelemtry(self):
        if self.telemtry is not None:
            return self.telemtry.copy()
        return None
    
    def run(self):
        self.main()

    def kill(self):
        self.keepRunning = False
        time.sleep(0.1)
    
    
    def main(self):
        
        sx,sy=config.cam_res_rgbx,config.cam_res_rgby
        
        #main_camera_fd=None
        message_dict={}
        rcv_cnt=0
        images = [None, None]
        sonar_images = [None, None]
        bmargx,bmargy=config.viewer_blacks
        print('rovDataHandler running...')
        
        while self.keepRunning:
            time.sleep(0.0001)
            if not self.rawVideo:
                if len(select([self.imgSock],[],[],0.003)[0]) > 0:
                    # print('camera')
                    data, addr = self.imgSock.recvfrom(1024*64)
                    self.curFrameId, self.curExposure, encIm = pickle.loads(data)
                    img = cv2.imdecode(encIm, 1)
                    
                    images = [img]
                    rcv_cnt += 1

                if len(select([self.sonar_imgSock],[],[],0.003)[0]) > 0:
                    # print('sonar')                    
                    data, addr = self.sonar_imgSock.recvfrom(1024*64)
                    self.sonar_curFrameId, self.sonar_curExposure, encIm = pickle.loads(data)
                    sonar_img = cv2.imdecode(encIm, 1)
                    
                    sonar_images = [sonar_img]
                    rcv_cnt += 1

            self.telemtry = None
            while True:
                
                time.sleep(0.0001)
                socks = zmq.select(self.subs_socks,[],[],0.001)[0]
                if len(socks)==0: #flush msg buffer
                    break
                for sock in socks:

                    ret = sock.recv_multipart()
                    topic = ret[0]
                    if topic not in [zmq_topics.topic_stereo_camera, zmq_topics.topic_sonar]:
                        topic, data = ret
                        data = pickle.loads(ret[1])
                        message_dict[topic] = data
                        self.telemtry = message_dict.copy()
                        
                        #if topic == zmq_topics.topic_system_state:
                        #    import ipdb; ipdb.set_trace()
                        
                        if self.pubData:
                            self.socket_pub.send_multipart([ret[0],ret[1]])
                        
                        if zmq_topics.topic_tracker_result == topic:
                            #print('trck data res:', data)
                            try:
                                if data[1][0] < 0:
                                    message_dict.pop(zmq_topics.topic_tracker_result)
                            except:
                                import traceback
                                traceback.print_exc()
                                #import ipdb; ipdb.set_trace()
                                
                    # elif self.rawVideo and topic in [zmq_topics.topic_sonar]:  # zmq_topics.topic_stereo_camera
                    elif self.rawVideo and topic in [zmq_topics.topic_stereo_camera, zmq_topics.topic_sonar]:
                        print(topic)
                        self.curFrameId, imShape, self.curExposure, ts = pickle.loads(ret[1])
                        #print('<><>', self.curFrameId, imShape, ts)
                        imRaw = np.frombuffer(ret[-1], dtype='uint8').reshape(imShape)
                        if topic == zmq_topics.topic_stereo_camera:
                            images = [imRaw]
                        if topic == zmq_topics.topic_sonar:
                            sonar_images = [imRaw]
                        
    
            showIm = None
            if images[0] is not None:
                #images[0] = cv2.cvtColor(images[0], cv2.COLOR_BGR2RGB)
                fmt_cnt_l=image_enc_dec.decode(images[0])
                draw_mono(images[0],message_dict,fmt_cnt_l)
                
                showIm = images[0]
            
            if showIm is not None:
                #self.rovViewer.update_image(showIm)
                self.image = showIm
                images[0] = None
                if 0:
                    cv2.imshow('3dviewer', showIm)
                    cv2.waitKey(10)

            # sonar
            sonar_showIm = None
            if sonar_images[0] is not None:
                #images[0] = cv2.cvtColor(images[0], cv2.COLOR_BGR2RGB)
                fmt_cnt_l=image_enc_dec.decode(sonar_images[0])
                draw_sonar(sonar_images[0],message_dict,fmt_cnt_l)
                
                sonar_showIm = sonar_images[0]
            
            if sonar_showIm is not None:
                #self.rovViewer.update_image(showIm)
                self.sonar_image = sonar_showIm
                sonar_images[0] = None
                # if 0:
                #     cv2.imshow('3dviewer', showIm)
                #     cv2.waitKey(10)
                
        print('bye bye!')


### message mapping from joystick to gui
armDisarmMsg = [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]

recordMsg = [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0]
attHoldMsg = [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0] 
depthHoldMsg = [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]

lightDownMsg = [0, 0, 0, 0, 0, 0, 0.0, 1.0]
lightUpMsg = [0, 0, 0, 0, 0, 0, 0.0, -1.0]
neutralHatMsg = [0, 0, 0, 0, 0, 0, 0.0, 0]
focusNearMsg = [0, 0, 0, 0, 0, 0, -1, 0]
focusFarMsg = [0, 0, 0, 0, 0, 0, 1, 0]

attHoldMsg   = [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
depthHoldMsg = [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]



class checkListForm(object):
    def __init__(self,master):
        
        #TODO: kill hw_gate.py on ROV
        self.pub_sock = utils.publisher(zmq_topics.topic_check_thrusters_comand_port)
        self.rovGuiCommandPublisher = rovGuiCommandPublisher
        
        top=self.top = Toplevel(master)
        
        top.protocol("WM_DELETE_WINDOW", self.cleanup)
        
        top.attributes('-topmost', True)
        top.title("ROV Check List")
        #top.geometry('880x700')
        
        path = "frame-numberings.jpg"
        self.img = Image.open(path)
        width = 400
        height = 350
        rowHeight = 29
        try: # new PIL version
            self.img = ImageTk.PhotoImage(self.img.resize((width, height), Image.Dither.NONE))
        except:
            self.img = ImageTk.PhotoImage(self.img.resize((width, height), Image.NONE))
        
        lbl = Label(top, image=self.img, width=width, height=height, borderwidth=2,
                    highlightbackground="white")
        lbl.image = self.img
        lbl.place(x=430,y=250)
        
        curRow = 1
        self.l = Label(top,text="CAUTION! - motors are running during test")
        self.l.grid(column=1, row=curRow, columnspan=4, sticky='w')  #.place(x=1, y=1)
        curRow += 1
        
        headreFontSize = 11
        
        
        self.l = Label(top,text="Camera Test")
        self.l.configure(font=("Helvetica", headreFontSize, "bold"))
        self.l.grid(column=1, row=curRow, columnspan=4, sticky='w')  #.place(x=1, y=1)
        
        curRow += 1
        
        self.checkVar = IntVar()
        self.checkVar.set(1)
        
        self.Check = Checkbutton(top, variable=self.checkVar, onvalue=0, offvalue=1, text="Is live image?")
        self.Check.grid(column=1, row=curRow, sticky='w')
        
        curRow += 1
        
        self.l = Label(top,text="Set exposure to manual")
        self.l.grid(column=1, row=curRow, columnspan=2, sticky='w')  #.place(x=1, y=1)
        
        curRow += 1
        
        self.l = Label(top,text="Set exposure to 1")
        self.l.grid(column=1, row=curRow, columnspan=1, sticky='w')  #.place(x=1, y=1)
        
        self.checkVar = IntVar()
        self.checkVar.set(1)
        
        self.Check = Checkbutton(top, variable=self.checkVar, onvalue=0, offvalue=1, text="Dark image OK")
        self.Check.grid(column=2, columnspan=2, row=curRow, sticky='w')
        
        curRow += 1
        
        self.l = Label(top,text="Set exposure to 99")
        self.l.grid(column=1, row=curRow, columnspan=1, sticky='w')  #.place(x=1, y=1)
        
        self.checkVar = IntVar()
        self.checkVar.set(1)
        
        self.Check = Checkbutton(top, variable=self.checkVar, onvalue=0, offvalue=1, text="Bright image OK")
        self.Check.grid(column=2, columnspan=2, row=curRow, sticky='w')
        
        curRow += 1
        
        self.l = Label(top,text="Set auto exposure")
        self.l.grid(column=1, row=curRow, columnspan=1, sticky='w')  #.place(x=1, y=1)
        
        self.checkVar = IntVar()
        self.checkVar.set(1)
        
        self.Check = Checkbutton(top, variable=self.checkVar, onvalue=0, offvalue=1, text="auto exposure OK")
        self.Check.grid(column=2, columnspan=2, row=curRow, sticky='w')
        
        curRow += 1
        
        self.l = Label(top,text="Inertial Test")
        self.l.configure(font=("Helvetica", headreFontSize, "bold"))
        self.l.grid(column=1, row=curRow, columnspan=4, sticky='w')  #.place(x=1, y=1)
        
        curRow += 1
        
        self.l = Label(top,text="IMU test - pitch: nose down/up\n\troll: tilt right/left:")
        self.l.grid(column=1, row=curRow, columnspan=4, sticky='w')  #.place(x=1, y=1)
        
        
        curRow += 1
        self.checkVar = IntVar()
        self.checkVar.set(1)
        
        self.Check = Checkbutton(top, variable=self.checkVar, onvalue=0, offvalue=1, text="IMU OK")
        self.Check.grid(column=2, columnspan=2, row=curRow, sticky='w')
        
        curRow += 1

        self.l = Label(top,text="IMU test - check mag. 90-90 (yawing):")
        self.l.grid(column=1, row=curRow, columnspan=4, sticky='w')  #.place(x=1, y=1)
        
        
        curRow += 1
        self.checkVar = IntVar()
        self.checkVar.set(1)
        
        self.Check = Checkbutton(top, variable=self.checkVar, onvalue=0, offvalue=1, text="Mag. OK")
        self.Check.grid(column=2, columnspan=2, row=curRow, sticky='w')
        
        curRow += 1
        #top.grid_rowconfigure(curRow, minsize=rowHeight)
        #curRow += 1
        
        self.l = Label(top,text="Motors Test")
        self.l.configure(font=("Helvetica", headreFontSize, "bold"))
        self.l.grid(column=1, row=curRow, columnspan=4, sticky='w')  #.place(x=1, y=1)
        
        curRow += 1

        '''
        self.motorsTest=Button(top, text='motor Test', command=lambda motId=-1: self.runMotorTest(motId) )
        self.motorsTest.grid(column=1, row=curRow, sticky='w')
        
        self.checkVar = IntVar()
        self.checkVar.set(1)
        
        self.Check = Checkbutton(top, variable=self.checkVar, onvalue=0, offvalue=1, text="motors OK")
        self.Check.grid(column=2, row=curRow, sticky='w')
        
        curRow +=1
        colIxd = 1
        
        
        for motIdx in range(0,8):
            if motIdx%2 == 0:
                curRow += 1
                colIxd = 1
        
            #self.tmpBtn = Button(top, text='M-%d'%(motIdx+1), command=lambda curMotId=motIdx+1: self.runMotorTest(curMotId) )
            self.tmpBtn = Scale(top, from_=1400, to=1600, tickinterval=10, orient=HORIZONTAL, showvalue=False) #, command=lambda curMotId=motIdx+1: self.runMotorTest(curMotId))
            self.tmpBtn.set(1500)
            self.tmpBtn.coords(value=None)
            self.tmpBtn.grid(column=colIxd, row=curRow, sticky='w')
            colIxd += 1
            
            self.checkVar = IntVar()
            self.checkVar.set(1)
            
            self.Check = Checkbutton(top, variable=self.checkVar, onvalue=0, offvalue=1, text="M%d-OK"%(motIdx+1) )
            self.Check.grid(column=colIxd, row=curRow, sticky='w')
            colIxd += 1
        '''  
        self.mototValues = []
        for motIdx in range(0,8):
             if motIdx%4 == 0:
                 curRow += 2
                 colIxd = 1
             current_value = DoubleVar()
             #self.tmpBtn = Button(top, text='M-%d'%(motIdx+1), command=lambda curMotId=motIdx+1: self.runMotorTest(curMotId) )
             tmpBtn = Scale(top, from_=1350, 
                                      to=1650, 
                                      orient=VERTICAL, 
                                      label="M-%d"%(motIdx+1), 
                                      showvalue=True, 
                                      resolution=5,
                                      variable=current_value,
                                      command = self.runMotorTest )
                                      #command=lambda curMotId=motIdx+1, B=0: self.runMotorTest(B, curMotId))
             tmpBtn.set(1500)
             self.mototValues.append(current_value)

             tmpBtn.grid(column=colIxd, row=curRow, sticky='w')
             #colIxd += 1
             
             self.checkVar = IntVar()
             self.checkVar.set(1)
             
             self.Check = Checkbutton(top, variable=self.checkVar, onvalue=0, offvalue=1, text="M%d-OK"%(motIdx+1) )
             self.Check.grid(column=colIxd, row=curRow+1, sticky='w')
             colIxd += 1
        
        curRow += 1
        top.grid_rowconfigure(curRow, minsize=rowHeight)
        curRow += 1
        
        self.l = Label(top,text="Peripherals Test")
        
        self.l.configure(font=("Helvetica", headreFontSize, "bold"))
        self.l.grid(column=1, row=curRow, columnspan=4, sticky='w')  #.place(x=1, y=1)
        curRow += 1
        
        self.servoTest=Button(top, text='Focus test', command=self.runFocusTest)
        self.servoTest.grid(column=1, row=curRow, sticky='w')
        
        self.checkVar = IntVar()
        self.checkVar.set(1)
        
        self.Check = Checkbutton(top, variable=self.checkVar, onvalue=0, offvalue=1, text="Servo OK")
        self.Check.grid(column=2, row=curRow, sticky='w')
        
        
        curRow +=1
        self.ledsTest = Button(top, text='Leds test', command=self.runLedsTest)
        self.ledsTest.grid(column=1, row=curRow, sticky='w')
        
        self.checkVar = IntVar()
        self.checkVar.set(1)
        
        self.Check = Checkbutton(top, variable=self.checkVar, onvalue=0, offvalue=1, text="Leds OK")
        self.Check.grid(column=2, row=curRow, sticky='w')
        
        curRow +=1
       
        self.checkVar = IntVar()
        self.checkVar.set(1)
        
        self.Check = Checkbutton(top, variable=self.checkVar, onvalue=0, offvalue=1, text="Check disk space")
        self.Check.grid(column=1, row=curRow, sticky='w')
        
        curRow +=1
        
        top.grid_rowconfigure(curRow, minsize=rowHeight//2)
        curRow += 1
        
        self.doneBtn=Button(top,text='Done',command=self.cleanup)
        self.doneBtn.grid(column=1, row=curRow, sticky='w')
        
        
        #print("calculate form height: %d"%(curRow*rowHeight))
        top.geometry('860x%d'%(curRow*rowHeight) )
        
        self.motorsTestSent = False
        self.motorsTestSentTic = time.time()
        
        self.startFocusTest = False
        self.focusVal = 850
        self.focusSendTic = time.time()
        
        self.main()
        
        
    def runMotorTest(self, val):
        #TODO: call esp test function on ROV
        
        pwms = []
        for X in self.mototValues: 
            pwms.append( int( X.get() ) )

        #print('-->', pwms)
        if any((True for x in pwms if x != 1500)):
            tic = time.time()
            pwms = (1500-np.array(pwms))/800
            print('-->', pwms)
            pwms = np.clip(pwms,-1,1)
            #print('-->', pwms)
            self.pub_sock.send_multipart([zmq_topics.topic_check_thrusters_comand, pickle.dumps((tic,list(pwms)))])
            self.motorsTestSent = True
            self.motorsTestSentTic = time.time()
    
    def sendFocusVal(self, val):
        print('new focus PWM: %d'%val)
        data = pickle.dumps(val, protocol=3)
        self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_focus_controller, data])
        self.focusSendTic = time.time()

            
    def runFocusTest(self):
        
        ## send focus command
        self.startFocusTest = not self.startFocusTest
        if self.startFocusTest:
            self.focusVal = 850
           
        
    def runLedsTest(self):
        #TODO: call esp test function on ROV
        print("TBD: Leds test...")
    
    def main(self):
        
        if self.motorsTestSent and (time.time() - self.motorsTestSentTic) > 3: 
            pwms = [1500]*8
            print('-stop motors->', pwms)
            tic = time.time()
            pwms = (1500-np.array(pwms))/800
            #print('-->', pwms)
            pwms = np.clip(pwms,-1,1)
            #print('-->', pwms)
            self.pub_sock.send_multipart([zmq_topics.topic_check_thrusters_comand, pickle.dumps((tic,list(pwms)))])
            self.motorsTestSent = False
            self.motorsTestSentTic = time.time()
            # update GUI 
            for X in self.mototValues:
                X.set(1500)
                
        if self.startFocusTest and (time.time() - self.focusSendTic) > 0.5:
            self.sendFocusVal(self.focusVal)
            self.focusVal += 100
            if self.focusVal >= 2250:
                self.startFocusTest = False
                
            
                
        self.top.after(25, self.main)
        
    def cleanup(self):
        try:
            import tkcap
            cap = tkcap.CAP(self.top)     # master is an instance of tkinter.Tk

            picturePath = os.path.join(os.getenv("HOME"), "Pictures/checkList")
            if not os.path.exists(picturePath):
                os.system('mkdir -p %s'%picturePath)
            imgName = time.strftime("CL_%Y%m%d_%H%M%S.png", time.localtime())
            imgPath = os.path.join(picturePath, imgName)
            #region = cap.get_region()
            cap.capture(imgPath)       # Capture and Save the screenshot of the tkiner window

        except:
            print('To record the check list - please install the following pkgs: \npip install tkcap \nsudo apt-get install scrot')
        print("clean form...")
        self.pub_sock.close()
        self.top.destroy()




class recRunProp(object):
    def __init__(self,master):
        top=self.top = Toplevel(master)
        
        self.l = Label(top,text="Run record ")
        self.l.pack()
        
        self.saveTiffVar = IntVar()
        self.saveTiffVar.set(1)
        
        self.saveTiff = Checkbutton(top, variable=self.saveTiffVar, onvalue=0, offvalue=1, text="save tiffs")
        self.saveTiff.pack()
        
        
        self.saveAviVar = IntVar()
        self.saveAviVar.set(1)
        
        self.saveAvi = Checkbutton(top, variable = self.saveAviVar, onvalue=0, offvalue=1, text="save avi")
        self.saveAvi.pack()
        
        self.freeRunVar = IntVar()
        self.freeRunVar.set(1)
        
        self.freeRun = Checkbutton(top, variable = self.freeRunVar, onvalue=0, offvalue=1, text="free run")
        self.freeRun.pack()
        
        self.l = Label(top,text="skip frames")
        self.l.pack()
        
        self.skipFrames = Entry(top)
        self.skipFramesVar = "-1"
        self.skipFrames.insert(0, self.skipFramesVar)
        self.skipFrames.pack()
        
        
        self.b=Button(top,text='Run',command=self.cleanup)
        self.b.pack()
        
    def cleanup(self):
        self.skipFramesVar = self.skipFrames.get()
        self.top.destroy()


# this class is the base of our GUI
class rovViewerWindow(Frame):
    def __init__(self, parent=None, **kw):
        super().__init__(**kw)
        self.parent = parent

        # init attributes
        
        self.checkInertial = IntVar()
        self.checkInertial.set(1)
        
        self.checkDepthControl = IntVar()
        self.checkDepthControl.set(1)
        self.checkThrusters = IntVar()
        self.checkThrusters.set(1)
        self.checkPitchControl = IntVar()
        self.checkPitchControl.set(1)
        self.checkRollControl = IntVar()
        self.checkRollControl.set(1)
        self.checkYawControl = IntVar()
        self.checkYawControl.set(1)
        self.checkRecorder = IntVar()
        self.checkRecorder.set(1)
        
        self.OpencvWinInit = False
        self.image = None

        self.controllerChbx = {'depth':self.checkDepthControl, 'pitch':self.checkPitchControl, 'roll':self.checkRollControl, 'yaw':self.checkYawControl, 'thrusters':self.checkThrusters}

        
        self.resize_called = True
        
        self.myStyle = {'fg': 'black', 'bg': 'LightSteelBlue', 'buttonBg': 'gray90', 'buttonFg': 'black',
                     'activeDisplayButtonFg': 'gray40', 'activeDisplayButtonBg': 'pink',
                     'buttonBgSoft': 'slategrey', 'buttonFgSoft': 'white', 'activeSoftButtonBg': 'gray50',
                     'buttonBgControl': 'green', 'buttonFgControl': 'ghostwhite', 'btnHighlight': 'pink',
                     'disabled_fg': 'gray26', 'select_bg': 'pink', 'activeButtonBg': 'gray70',
                     'activeControlButtonBg': 'gray50'}

        self.img = None
        self.last_pressed_button = 'disarm'
        
        self.dPitchVal = None
        self.dDepthVal = None
        self.dYawVal = None
        
        self.dRtPitchVal = None
        self.dRtDepthVal = None
        self.dRtYawVal = None
        
        self.initRtColPlace = None
        
        self.TFont = ("Courier", 14)
        self.TextboxFont = ("Courier", 12)
        self.HeaderFont = ("Courier", 16, "underline")
        
        self.cvWindow = False
        self.cvWinName = "ROViewer"
        self.ROVHandler = rovDataHandler(self)
        self.ROVHandler.start()

        self.initX = 15
        self.initY = 660
        self.colWidth = 100
        self.colButtonWidth = 120
        self.rowHeight = 30 # more space - 35
        
        self.plotHistory = 500
        self.plotMsgs = {}
        self.frameId = -1
        
        self.runPlotsFlag = True
        
        # create widgets
        self.focusVal = -1
        self.exposureVal = -1
        
        self.make_widgets()
        self.bind_widgets_events()
        self.maximize_with_title()
        self.set_style()
        
        self.updateGuiData()
        self.rovGuiCommandPublisher = rovGuiCommandPublisher #utils.publisher(zmq_topics.topic_gui_port)
        self.armClicked = False
        self.recClicked = False
        self.attMessage = {'dDepth':0.0, 'dPitch': 0.0, 'dYaw':0.0}
        
        self.updatePids()
        
        print(' display layer init done ')

        
    
    def quit(self):
        self.ROVHandler.kill()
        self.parent.quit()
    
        
    def maximize_with_title(self):
        self.parent.title("ROV viewer")
        w, h = self.parent.winfo_screenwidth(), self.parent.winfo_screenheight()
        self.parent.geometry("%dx%d+0+0" % (w - 20, h - 20))

    def set_style(self):
        #self.parent.geometry('1600x900+0+0')
        self.parent.configure(background=self.myStyle['bg'])

    def resize(self, event):
        self.resize_called = True

    def create_label(self, name, display_text, n_col, n_row, width, centered):
        if centered:
            lbl = Label(self.parent, text=display_text, width=width)
        else:
            lbl = Label(self.parent, text=display_text, anchor="w", width=width)
        lbl.grid(column=n_col, row=n_row)
        lbl.configure(background=self.myStyle['bg'], foreground=self.myStyle['fg'])
        lbl.config(font=self.TFont)
        self.myStyle[name] = lbl

    def create_label_pair(self, name, display_text, n_col, n_row):
        first_name = "{}label".format(name)
        second_name = "{}text".format(name)
        self.myStyle[first_name] = Label(self.parent, text=display_text, anchor="w", width=15)
        self.myStyle[second_name] = Label(self.parent, text="n/a", width=18, anchor="w")
        self.myStyle[first_name].grid(column=n_col, row=n_row)
        self.myStyle[second_name].grid(column=n_col + 1, row=n_row)
        self.myStyle[first_name].configure(background=self.myStyle['bg'], foreground=self.myStyle['fg'])
        self.myStyle[second_name].configure(background=self.myStyle['bg'], foreground=self.myStyle['fg'])

        self.myStyle[first_name].config(font=self.TFont)
        self.myStyle[second_name].config(font=self.TFont)

        #print('-->', display_text, n_col, n_row)
        self.myStyle[first_name].place(x=self.initX+(n_col-1)*self.colWidth, y=self.initY+(n_row-1)*self.rowHeight)
        self.myStyle[second_name].place(x=self.initX+(n_col)*self.colWidth, y=self.initY+(n_row-1)*self.rowHeight)


    def create_main_col_row_labels(self):
        for number in range(0, 10):
            lbl = Label(self.parent, text=" ", anchor="e", width=1)
            lbl.grid(column=number, row=0)
            lbl.configure(background=self.myStyle['bg'], foreground=self.myStyle['fg'])
            lbl = Label(self.parent, text=" ", anchor="e", width=1)
            lbl.grid(column=0, row=number)
            lbl.configure(background=self.myStyle['bg'], foreground=self.myStyle['fg'])

    def create_single_label_header(self, name, display_text, n_col, n_row):
        first_name = "{}label1".format(name)
        self.myStyle[first_name] = Label(self.parent, text=display_text, anchor="w", width=1 + len(display_text))
        self.myStyle[first_name].grid(column=n_col, row=n_row, padx=5, pady=2)
        self.myStyle[first_name].configure(background=self.myStyle['bg'], foreground=self.myStyle['fg'])
        self.myStyle[first_name].config(font=self.HeaderFont)

    def create_label_header(self, name, display_text1, display_text2, display_text3, display_text4, display_text5,
                            n_col, n_row):
        first_name = "{}label1".format(name)
        second_name = "{}label2".format(name)
        third_name = "{}label3".format(name)
        fourth_name = "{}label4".format(name)
        fifth_name = "{}label5".format(name)

        self.myStyle[first_name] = Label(self.parent, text=display_text1, width=15) #, anchor="w")
        self.myStyle[second_name] = Label(self.parent, text=display_text2, width=10)
        self.myStyle[third_name] = Label(self.parent, text=display_text3, width=15)
        self.myStyle[fourth_name] = Label(self.parent, text=display_text4, width=15)
        self.myStyle[fifth_name] = Label(self.parent, text=display_text5, width=15)

        self.myStyle[first_name].grid(column=n_col, row=n_row)
        self.myStyle[second_name].grid(column=n_col + 1, row=n_row)
        self.myStyle[third_name].grid(column=n_col + 3, row=n_row)
        self.myStyle[fourth_name].grid(column=n_col + 5, row=n_row)
        self.myStyle[fifth_name].grid(column=n_col + 7, row=n_row)

        self.myStyle[first_name].configure(background=self.myStyle['bg'], foreground=self.myStyle['fg'])
        self.myStyle[second_name].configure(background=self.myStyle['bg'], foreground=self.myStyle['fg'])
        self.myStyle[third_name].configure(background=self.myStyle['bg'], foreground=self.myStyle['fg'])
        self.myStyle[fourth_name].configure(background=self.myStyle['bg'], foreground=self.myStyle['fg'])
        self.myStyle[fifth_name].configure(background=self.myStyle['bg'], foreground=self.myStyle['fg'])

        self.myStyle[first_name].config(font=self.HeaderFont)
        self.myStyle[second_name].config(font=self.HeaderFont)
        self.myStyle[third_name].config(font=self.HeaderFont)
        self.myStyle[fourth_name].config(font=self.HeaderFont)
        self.myStyle[fifth_name].config(font=self.HeaderFont)
   
    
    def create_text_box(self, name, label_text, display_text, n_col, n_row, textbox_width, stickyness='NESW'):
        first_name = "{}_label".format(name)
        second_name = "{}_textbox".format(name)
        self.myStyle[first_name] = Label(self.parent, text=label_text, anchor="w") #, width=15)
        self.myStyle[first_name].grid(column=n_col, row=n_row)
        self.myStyle[first_name].configure(background=self.myStyle['bg'], foreground=self.myStyle['fg'])
        self.myStyle[first_name].config(font=self.TFont)

        self.myStyle[second_name] = Entry(self.parent, borderwidth=1, relief="sunken", width=textbox_width, selectbackground=self.myStyle['select_bg'])
        self.myStyle[second_name].config(font=self.TextboxFont)
        self.myStyle[second_name].grid(row=n_row, column=n_col + 1, padx=2, pady=2, sticky=stickyness)

        self.myStyle[second_name].insert(END, display_text)
        #print('-->', label_text, n_col, n_row)
        self.myStyle[first_name].place(x=self.initX+(n_col-1)*self.colWidth, y=self.initY+(n_row-1)*self.rowHeight)
        self.myStyle[second_name].place(x=self.initX+(n_col)*self.colWidth, y=self.initY+(n_row-1)*self.rowHeight)

    def bind_widgets_events(self):
        
        self.myStyle['disp_image'].bind("<Button-1>", self.image_clicked)
        self.myStyle['disp_image'].bind("<Button-3>", self.grabImageEvent)
        self.myStyle['disp_image'].bind("<Button-2>", self.setAutoFocus)
        ## double click -> "<Double-1>"
        #self.myStyle['disp_image'].bind("<Button-2>", self.image_right_clicked)
        #self.myStyle['disp_image'].bind("<Button-3>", self.image_right_clicked)
        
        '''
        self.parent.bind("<Left>",  self.left_click_func)
        self.parent.bind("<Right>", self.right_click_func)
        self.parent.bind("<Up>",    self.up_click_func)
        self.parent.bind("<Down>",  self.down_click_func)
        self.parent.bind("<Prior>", self.page_up_click_func)
        self.parent.bind("<Next>",  self.page_down_click_func)
        self.parent.bind("<Key-7>", self.turn_left_click_func)
        self.parent.bind("<Key-9>", self.turn_right_click_func)
        '''

        self.parent.bind("<Key-a>", self.goLeft)
        self.parent.bind("<Key-d>", self.goRight)
        self.parent.bind("<Key-w>", self.goForward)
        self.parent.bind("<Key-s>", self.neutralCmd)
        self.parent.bind("<Key-x>", self.goBackwards)
        self.parent.bind("<Key-e>", self.yawRight)
        self.parent.bind("<Key-q>", self.yawLeft)
        self.parent.bind("<Key-c>", self.goDeeper)
        self.parent.bind("<Key-z>", self.goUpper)
        
        self.parent.bind("<F11>",   self.fullVideoScreenEvent)


    def updatePIds(self, pids):
        self.myStyle["K_textbox"].delete(0, END)
        self.myStyle["K_textbox"].insert(END, "{}".format(pids['K']) )
        self.myStyle["Kp_textbox"].delete(0, END)
        self.myStyle["Kp_textbox"].insert(END, "{}".format(pids['P']) )
        self.myStyle["Ki_textbox"].delete(0, END)
        self.myStyle["Ki_textbox"].insert(END, "{}".format(pids['I']) )
        self.myStyle["Kd_textbox"].delete(0, END)
        self.myStyle["Kd_textbox"].insert(END, "{}".format(pids['D']) )

    def depthSelect(self):
        if self.controllerChbx['depth'].get() == 0:
            self.selectController('depth')
            with open("../config_pid.json") as fid:
                data = json.load(fid)
            pids = data["config_pid"][0]['depth_pid']
            self.updatePIds(pids)
            
    def threustersSelect(self):
        if self.controllerChbx['thrusters'].get() == 0:
            self.selectController('thrusters')

    def pitchSelect(self):
        if self.controllerChbx['pitch'].get() == 0:
            self.selectController('pitch')
            with open("../config_pid.json") as fid:
                data = json.load(fid)
            pids = data["config_pid"][0]['pitch_pid']
            self.updatePIds(pids)
            
    
    def rollSelect(self):
        if self.controllerChbx['roll'].get() == 0:
            self.selectController('roll')
            with open("../config_pid.json") as fid:
                data = json.load(fid)
            pids = data["config_pid"][0]['roll_pid']
            self.updatePIds(pids)
            
            
    def yawSelect(self):
        if self.controllerChbx['yaw'].get() == 0:
            self.selectController('yaw')
            with open("../config_pid.json") as fid:
                data = json.load(fid)
            pids = data["config_pid"][0]['yaw_pid']
            self.updatePIds(pids)
            
            
    def selectController(self, ctrl):
        for key in self.controllerChbx:
            if key != ctrl:
                self.controllerChbx[key].set(1)
        self.initPlots()
                
            
            


    def updateDepth(self, event):
        chars = event.widget.get()
        try:
            val = float(chars.strip())
            print('new depth is %0.2f'%val)
            desiredDepth = val
            self.attMessage['dYaw'] = None
            self.attMessage['dPitch'] = None
            self.attMessage['dDepth'] = desiredDepth
            data = pickle.dumps(self.attMessage, protocol=3)
            self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_depthAtt, data])
        except:
            print('failed to load value')
        
        
    def updatePitch(self, event):
        chars = event.widget.get()
        try:
            val = float(chars.strip())
            print('new pitch is %0.2f'%val)
            desiredPitch = val
            self.attMessage['dDepth'] = None
            self.attMessage['dYaw'] = None
            self.attMessage['dPitch'] = desiredPitch
            data = pickle.dumps(self.attMessage, protocol=3)
            self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_depthAtt, data])
        except:
            print('failed to load value')
        
    def updateFocus(self, event):
        chars = event.widget.get()
        try:
            val = min(max(int(chars.strip()),850),2250)
            self.myStyle['focusCmd_textbox'].delete(0, END)
            self.myStyle['focusCmd_textbox'].insert(0,str(val))
            print('new focus PWM: %d'%val)
            data = pickle.dumps(val, protocol=3)
            self.focusVal = -1 # update gui to updated focus value from messages
            self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_focus_controller, data])
            ## send focus command
        except:
            print('failed to load value')
            
    def updateExposure(self, event):
        chars = event.widget.get()
        try:
            #pass
            val = min(max(float(chars.strip()),0),300)
            self.myStyle['exposureCMD_textbox'].delete(0, END)
            self.myStyle['exposureCMD_textbox'].insert(0,str(val))
            print('new exposure: %f'%val)
            data = pickle.dumps(val, protocol=3)
            #self.exposureVal = -1 # update gui to updated focus value from messages
            self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_exposureVal, data])
            # send focus command
        except:
            print('failed to load value')

    def updateYaw(self, event):
        chars = event.widget.get()
        try:
            val = float(chars.strip())
            print('new yaw is %0.2f'%val)
            desiredYaw = val
            self.attMessage['dDepth'] = None
            self.attMessage['dYaw'] = desiredYaw
            self.attMessage['dPitch'] = None
            data = pickle.dumps(self.attMessage, protocol=3)
            self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_depthAtt, data])
        except:
            print('failed to load value')
        

    def create_button(self, name, display_text, n_col, n_row, callback, tooltip=""):
        button_name = "{}_button".format(name)
        _btn = Button(self.parent, text=display_text, command=callback, width=13,
                      activebackground=self.myStyle['activeButtonBg'])
        _btn.grid(column=n_col+1, row=n_row)
        _btn.config(background=self.myStyle['buttonBg'], foreground=self.myStyle['buttonFg'], font=self.TFont)
        self.myStyle[button_name] = _btn

        #print('-->', name, n_col, n_row)
        self.myStyle[button_name].place(x=self.initX+(n_col-1)*self.colWidth, y=self.initY+(n_row-1)*self.rowHeight)
        if len(tooltip) > 0:
            self.addTooltip(self.myStyle[button_name], tooltip) 


    def grabImageEvent(self, event):
        if self.image is not None:
            picturePath = os.path.join(os.getenv("HOME"), "Pictures/roViewer")
            if not os.path.exists(picturePath):
                os.system('mkdir -p %s'%picturePath)
            imgName = time.strftime("roViewer_%Y%m%d_%H%M%S.png", time.localtime())
            imgPath = os.path.join(picturePath, imgName)
            print('image saved, %s'%imgPath)
            im2save = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            cv2.imwrite(imgPath, im2save, [cv2.IMWRITE_PNG_COMPRESSION, 0])


    def image_clicked(self, event):
        if self.img is None:
            return
        try:
            tm_img = time.gmtime()

            obj = self.myStyle['disp_image']

            x = event.x
            y = event.y

            print('clicked x=%d, y=%d'%(x,y))
            # ImageGrab.grab().crop((x, y, width, height)).save(img_file)
            print('--->', {'trackPnt':(x,y), 'frameId':self.frameId } )
            msg = [zmq_topics.topic_gui_start_stop_track, pickle.dumps({'trackPnt':(x,y), 'frameId':self.frameId } , protocol=3)]
            self.rovGuiCommandPublisher.send_multipart(msg)
            
        except Exception as err:
            print(err)
            
    def setAutoFocus(self, event):
        print('run auto focus')
        data = pickle.dumps('run auto focus...', protocol=3)
        self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_autoFocus, data])
        
        
    def update_image(self):
        
        self.frameId, rawImg = self.ROVHandler.getNewImage()
        if rawImg is not None:
            #self.img = Image.open(io.BytesIO(img)) ## jpg stream
            self.image = rawImg.copy()
            img = Image.fromarray(rawImg)
            resolution = (self.myStyle['disp_image']['width'], self.myStyle['disp_image']['height'])
            self.img = ImageTk.PhotoImage(img.resize(resolution))
            #import ipdb; ipdb.set_trace() 
            self.myStyle['disp_image'].configure(image=self.img)
            self.myStyle['disp_image'].image = self.img

            # self.myStyle['disp_image_sonar'].configure(image=self.img)
            # self.myStyle['disp_image_sonar'].image = self.img
            
            if self.cvWindow:
                if not self.OpencvWinInit:
                    self.initOpencvWin(True)
                rawImg = cv2.cvtColor(rawImg, cv2.COLOR_BGR2RGB)
                cv2.imshow(self.cvWinName, rawImg)
                key = cv2.waitKey(1)
                if key&0xff == ord('q') or key == 200: # 200 -> F11
                    self.initOpencvWin(False)
                    self.cvWindow = False

        self.parent.after(10, self.update_image)


    def update_sonar_image(self):
        
        self.frameId, rawImg = self.ROVHandler.getNewSonarImage()
        if rawImg is not None:
            #self.img = Image.open(io.BytesIO(img)) ## jpg stream
            self.sonar_image = rawImg.copy()
            img = Image.fromarray(rawImg)
            resolution = (self.myStyle['disp_image_sonar']['width'], self.myStyle['disp_image_sonar']['height'])
            self.sonar_img = ImageTk.PhotoImage(img.resize(resolution))
            
            # self.myStyle['disp_image'].configure(image=self.img)
            # self.myStyle['disp_image'].image = self.img

            self.myStyle['disp_image_sonar'].configure(image=self.sonar_img)
            self.myStyle['disp_image_sonar'].image = self.sonar_img
            
            if self.cvWindow:
                if not self.OpencvWinInit:
                    self.initOpencvWin(True)
                rawImg = cv2.cvtColor(rawImg, cv2.COLOR_BGR2RGB)
                cv2.imshow(self.cvWinName, rawImg)
                key = cv2.waitKey(1)
                if key&0xff == ord('q') or key == 200: # 200 -> F11
                    self.initOpencvWin(False)
                    self.cvWindow = False

        self.parent.after(10, self.update_sonar_image)

    def addTooltip(self, widget, toolTip):
        try: 
            #tip = ListboxToolTip(widget, ["Hello", "world"])
            tip = ToolTip(widget, toolTip)
            #import ipdb; ipdb.set_trace()
        except:
            print('No tooltip available...')

    def make_image(self, name, col, row, x, y, char_width, char_height, update_function):
        path = "rov.jpg"
        self.img = Image.open(path)
        try: # new PIL version
            self.img = ImageTk.PhotoImage(self.img.resize((char_width, char_height), Image.Dither.NONE))
        except:
            self.img = ImageTk.PhotoImage(self.img.resize((char_width, char_height), Image.NONE))

        lbl = Label(self.parent, image=self.img, width=char_width, height=char_height, borderwidth=2,
                    highlightbackground="white")
        lbl.image = self.img
        lbl.grid(row=0, column=0) #, columnspan=width, rowspan=height, pady=5, padx=5, sticky="nw") #, sticky="nsew")
        self.myStyle[name] = lbl
        self.myStyle[name].place(x=x,y=y)

        self.addTooltip(self.myStyle[name], " Left click -> start/stop track \n Middle click -> auto focus \n Right click -> snap shot")

        update_function()


    def create_control_button(self, name, display_text, n_col, n_row, callback, toolTip = ""):
        button_name = "{}_button".format(name)
        btn = Button(self.parent, text=display_text, command=callback, width=9,
                     activebackground=self.myStyle['activeControlButtonBg'])
        #btn.grid(column=n_col, row=n_row)
        btn.config(background=self.myStyle['buttonBgControl'], foreground=self.myStyle['buttonFgControl'],
                   font=self.TFont)
        self.myStyle[button_name] = btn

        if len(toolTip) > 0:
            pass 
            #balloon = Balloon(self.parent, bg="white", title="Help")
            #balloon.bind_widget(self.myStyle[button_name], balloonmsg= toolTip)
        
        self.myStyle[button_name].place(x=self.initX+(n_col-1)*self.colButtonWidth, y=self.initY+(n_row-1)*self.rowHeight)


    def create_checkbox_button(self, name, display_text, n_col, n_row, var, anchor):
        checkbox = Checkbutton(self.parent, variable=var, onvalue=0, offvalue=1, text=display_text)
        checkbox.grid(column=n_col, row=n_row) #, sticky=anchor)
        checkbox.config(background=self.myStyle['bg'], foreground=self.myStyle['fg'], font=self.TFont)
        self.myStyle[name] = checkbox

        self.myStyle[name].place(x=self.initX+(n_col-1)*self.colWidth, y=self.initY+(n_row-1)*self.rowHeight)

    
    def autoExposure(self):
        print('auto exp. command')
        self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_toggle_auto_exp, pickle.dumps(b'', protocol=3)])
        
    def incExp(self):
        print('increase exposure command')
        self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_inc_exp, pickle.dumps(b'', protocol=3)])
        
    def decExp(self):
        print('decrease exposure command')
        self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_dec_exp, pickle.dumps(b'', protocol=3)])
        
        
    def autoGain(self):
        print('auto gain command')
        self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_toggle_auto_gain, pickle.dumps(b'', protocol=3) ])
    
    def goLeft(self):
        #TODO: send left movement command
        pass

    def goRight(self):
        #TODO: send right movement command
        pass
    
    def goForward(self):
        #TODO: send forward movement command
        pass
    
    def neutralCmd(self):
        #TODO: send no movement command (sticks at middle)
        pass
    
    def goBackwards(self):
        #TODO: send backwards movement command
        pass
    
    def yawRight(self):
        #TODO: send yaw-right movement command
        pass
    
    def yawLeft(self):
        #TODO: send yaw-left movement command
        pass
    
    def goDeeper(self):
        #TODO: send deeper movement command
        pass
    
    def goUpper(self):
        #TODO: send upper movement command
        pass
    

    def led_off(self):
        pass

    def led_low(self):
        pass

    def led_high(self):
        pass

    def updateGuiData(self):
        try:
            telemtry = self.ROVHandler.getTelemtry()
            if telemtry is not None:
                #print(telemtry.keys())
                rtData = {}
                motors = {}
                telemKeys = telemtry.keys()
                if zmq_topics.topic_imu in telemKeys:
                    data = telemtry[zmq_topics.topic_imu]
                    # print(data)
                    if self.dRtPitchVal is None:
                        self.myStyle['rtPitchtext'].config(text='%.2f°'%data['pitch'], font = ("Courier", 12))
                        if self.initRtColPlace is not None:
                            self.myStyle['rtPitchtext'].place(x = self.initRtColPlace )
                    else:
                        if self.initRtColPlace is None:
                           self.initRtColPlace =  int(self.myStyle['rtPitchtext'].place_info()['x']) 
                        self.myStyle['rtPitchtext'].config(text='%.1f/%.1f°'%(data['pitch'], self.dRtPitchVal ), font = ("Courier", 11) )
                        self.myStyle['rtPitchtext'].place(x = self.initRtColPlace - 30)
                    rtData['pitch'] = data['pitch']
                    
                    
                    self.myStyle['rtRolltext'].config(text='%.2f°'%data['roll'])
                    rtData['roll'] = data['roll']
                    
                    if self.dRtYawVal is None:
                        curYaw = data['yaw']
                        if curYaw < 0:
                            curYaw += 360
                            
                        self.myStyle['rtYawtext'].config(text='%.2f°'%data['yaw'], font = ("Courier", 12))
                        if self.initRtColPlace is not None:
                            self.myStyle['rtYawtext'].place(x = self.initRtColPlace )
                    else:
                        if self.initRtColPlace is None:
                           self.initRtColPlace =  int(self.myStyle['rtYawtext'].place_info()['x'])
                        self.myStyle['rtYawtext'].place(x = self.initRtColPlace - 30)
                        if self.dRtYawVal < 0:
                           self.dRtYawVal += 360
                        
                        if self.dRtYawVal < 0:
                           self.dRtYawVal += 360
                        curYaw = data['yaw']
                        if curYaw < 0:
                            curYaw += 360
                        self.myStyle['rtYawtext'].config(text='%.1f/%.1f°'%(curYaw, self.dRtYawVal ), font = ("Courier", 11) )
                    
                    rtData['yaw'] = data['yaw']
                    
                if zmq_topics.topic_depth in telemKeys:
                    data = telemtry[zmq_topics.topic_depth]
                    if self.dRtDepthVal is None:
                        self.myStyle['rtDepthtext'].config(text='%.2f[m]'%data['depth'], font = ("Courier", 12) )
                        if self.initRtColPlace is not None:
                            self.myStyle['rtDepthtext'].place(x = self.initRtColPlace )
                    else:
                        if self.initRtColPlace is None:
                           self.initRtColPlace =  int(self.myStyle['rtDepthtext'].place_info()['x'])
                        self.myStyle['rtDepthtext'].config(text='%.1f/%.1f[m]'%(data['depth'], self.dRtDepthVal ), font = ("Courier", 11) )
                        self.myStyle['rtDepthtext'].place(x = self.initRtColPlace - 20)
                        
                    topic = zmq_topics.topic_depth_hold_pid
                    rtData['depth'] = data['depth']
                if zmq_topics.topic_volt in telemtry:
                    data = telemtry[zmq_topics.topic_volt]
                    fg = 'black'
                    if data['V'] < 3.2*4:
                        fg = 'red'
                    self.myStyle['rtBatterytext'].config(text='%.2f[v]'%data['V'], foreground=fg)
                
                if zmq_topics.topic_system_state in telemKeys:
                    data = telemtry[zmq_topics.topic_system_state]
                    fg = 'black'
                    if data['diskUsage'] > 85:
                        bg='red'
                    self.myStyle['rtDisktext'].config(text='%d[%%]'%data['diskUsage'], foreground=fg)
                    #import ipdb; ipdb.set_trace()
                    if self.focusVal != data['focus']:
                        self.focusVal = data['focus']
                        self.myStyle["focusCmd_textbox"].delete(0, END)
                        self.myStyle["focusCmd_textbox"].insert(END, "{}".format(data['focus']) )
                    
                if zmq_topics.topic_motors_output in telemKeys:
                    data = telemtry[zmq_topics.topic_motors_output]
                    #print('---> motors: ', data['motors'])
                    for i in range(8):
                        motors[str(i)] = data['motors'][i]
                        
                    if 'thrusters' not in self.plotMsgs:
                        self.plotMsgs['thrusters'] = CycArr(self.plotHistory)
                    
                    self.plotMsgs['thrusters'].add(motors)
                
                
                if zmq_topics.topic_system_state in telemKeys:
                    system_state = telemtry[zmq_topics.topic_system_state]
                        
                    if 'ATT_HOLD' in system_state['mode']:
                        if zmq_topics.topic_att_hold_pitch_pid in telemKeys:
                            data = telemtry[zmq_topics.topic_att_hold_pitch_pid]
                            self.dRtPitchVal = data['T']
                        if zmq_topics.topic_att_hold_yaw_pid in telemKeys:
                            data = telemtry[zmq_topics.topic_att_hold_yaw_pid]
                            self.dRtYawVal = data['T']
                    else: 
                        self.dRtPitchVal = None
                        self.dRtYawVal = None
                    
                    if 'DEPTH_HOLD' in system_state['mode']:
                        
                        if zmq_topics.topic_depth_hold_pid in telemKeys:
                            data = telemtry[zmq_topics.topic_depth_hold_pid]
                            self.dRtDepthVal = data['T']
                    else:
                        self.dRtDepthVal = None
                                 
                if len(rtData.keys()) > 0: 
                    if 'rtData' not in self.plotMsgs:
                        self.plotMsgs['rtData'] = CycArr(self.plotHistory)
                    self.plotMsgs['rtData'].add(rtData)
                
            if self.ROVHandler.curExposure != self.exposureVal:
                self.exposureVal = self.ROVHandler.curExposure
                self.myStyle["exposureCMD_textbox"].delete(0, END)
                self.myStyle["exposureCMD_textbox"].insert(END, "%0.2f"%self.exposureVal) # {:.2f}".format(self.exposureVal) )

                
        except:
            import traceback
            traceback.print_exc()
            print('update gui data err')
            
        self.parent.after(25, self.updateGuiData)
    
    def cmdRecord(self):
        data = pickle.dumps(recordMsg, protocol=3)
        self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_diveModes, data])
        data = pickle.dumps(neutralHatMsg, protocol=3)
        self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_diveModes, data])
        self.update_button_active_command("record_button")
        
        if self.recClicked:
            self.myStyle["record_button"].config(foreground=self.myStyle['buttonFg'])
            self.myStyle["record_button"].config(activebackground=self.myStyle['activeButtonBg'])
        
        else:
            self.myStyle["record_button"].config(foreground=self.myStyle['activeDisplayButtonFg'])
            self.myStyle["record_button"].config(activebackground=self.myStyle['activeDisplayButtonBg'])
        self.recClicked = not self.recClicked
        
    
    
    def cmdArm(self):
        data = pickle.dumps(armDisarmMsg, protocol=3)
        self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_diveModes, data])
        data = pickle.dumps(neutralHatMsg, protocol=3)
        self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_diveModes, data])
        
        if self.armClicked:
            self.myStyle["arm_button"].config(foreground=self.myStyle['buttonFg'])
            self.myStyle["arm_button"].config(activebackground=self.myStyle['activeButtonBg'])
        
        else:
            self.myStyle["arm_button"].config(foreground=self.myStyle['activeDisplayButtonFg'])
            self.myStyle["arm_button"].config(activebackground=self.myStyle['activeDisplayButtonBg'])
        self.armClicked = not self.armClicked
    
    def cmdDepthHold(self):
        data = pickle.dumps(depthHoldMsg, protocol=3)
        self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_diveModes, data])
        data = pickle.dumps(neutralHatMsg, protocol=3)
        self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_diveModes, data])

    def cmdAttHold(self):
        data = pickle.dumps(attHoldMsg, protocol=3)
        self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_diveModes, data])
        data = pickle.dumps(neutralHatMsg, protocol=3)
        self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_diveModes, data])
        
    def cmdIncLights(self):
        data = pickle.dumps(lightUpMsg, protocol=3)
        self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_controller, data])
        data = pickle.dumps(neutralHatMsg, protocol=3)
        self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_controller, data])
        
    def cmdDecLights(self):
        data = pickle.dumps(lightDownMsg, protocol=3)
        self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_controller, data])
        data = pickle.dumps(neutralHatMsg, protocol=3)
        self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_controller, data])
        
    def focusFar(self):
        data = pickle.dumps(focusFarMsg, protocol=3)
        self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_controller, data])
        data = pickle.dumps(neutralHatMsg, protocol=3)
        self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_controller, data])
        
    def focusNear(self):
        data = pickle.dumps(focusNearMsg, protocol=3)
        self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_controller, data])
        data = pickle.dumps(neutralHatMsg, protocol=3)
        self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_controller, data])
    
    def updatePids(self):
        telemtry = self.ROVHandler.getTelemtry()
        if telemtry is not None:
            rollData = None
            pitchData = None
            yawData = None
            depthData = None
            if zmq_topics.topic_att_hold_roll_pid in telemtry:
                rollData = telemtry[zmq_topics.topic_att_hold_roll_pid]
                topic = zmq_topics.topic_att_hold_roll_pid
                if topic not in self.plotMsgs:
                        self.plotMsgs[topic] = CycArr(self.plotHistory)
                self.plotMsgs[topic].add(rollData)
                
            if zmq_topics.topic_att_hold_pitch_pid in telemtry:
                pitchData = telemtry[zmq_topics.topic_att_hold_pitch_pid]
                
                topic = zmq_topics.topic_att_hold_pitch_pid
                if topic not in self.plotMsgs:
                        self.plotMsgs[topic] = CycArr(self.plotHistory)
                self.plotMsgs[topic].add(pitchData)
                
            if zmq_topics.topic_att_hold_yaw_pid in telemtry:
                yawData = telemtry[zmq_topics.topic_att_hold_yaw_pid]
                
                topic = zmq_topics.topic_att_hold_yaw_pid
                if topic not in self.plotMsgs:
                        self.plotMsgs[topic] = CycArr(self.plotHistory)
                self.plotMsgs[topic].add(yawData)
                    
            if zmq_topics.topic_depth_hold_pid in telemtry:
                depthData = telemtry[zmq_topics.topic_depth_hold_pid]
                
                topic = zmq_topics.topic_depth_hold_pid
                if topic not in self.plotMsgs:
                        self.plotMsgs[topic] = CycArr(self.plotHistory)
                self.plotMsgs[topic].add(depthData)
            
            
            
            if (self.checkDepthControl.get() == 0) and (depthData is not None):
                self.plotData(zmq_topics.topic_depth_hold_pid, 'Depth control')
                
            if (self.checkPitchControl.get() == 0) and (pitchData is not None):
                self.plotData(zmq_topics.topic_att_hold_pitch_pid, 'Pitch control')
                
            if (self.checkRollControl.get() == 0) and (rollData is not None):
                self.plotData(zmq_topics.topic_att_hold_roll_pid, 'Roll control')
                
            if (self.checkYawControl.get() == 0) and (yawData is not None):
                self.plotData(zmq_topics.topic_att_hold_yaw_pid, 'Yaw control')
                
            if (self.checkThrusters.get() == 0) and ('thrusters' in self.plotMsgs):
                self.plotData('thrusters', 'Thrusters')
                
            if ( (self.checkYawControl.get() == 1) and 
                    (self.checkRollControl.get() == 1) and 
                    (self.checkPitchControl.get() == 1) and 
                    (self.checkDepthControl.get() == 1) and 
                    (self.checkThrusters.get() == 1) and 
                    'rtData' in self.plotMsgs ):
                    self.plotData('rtData', 'real time')
                    self.restPIDVals()
                
        self.parent.after(20, self.updatePids)
            
        
    def restPIDVals(self):
        self.myStyle["K_textbox"].delete(0, END)
        self.myStyle["Kp_textbox"].delete(0, END)
        self.myStyle["Ki_textbox"].delete(0, END)
        self.myStyle["Kd_textbox"].delete(0, END)
        
    
    def initPlots(self):
        
        self.ax1.clear()
        self.ax2.clear()
        
        self.hdls=[self.ax1.plot([1],'-b', alpha=0.3), self.ax1.plot([1],'-g', alpha=0.3), self.ax1.plot([1],'-r', alpha=0.3), self.ax1.plot([1],'-k', alpha=0.3)]
        
        #self.hdlsMotors=[self.ax1.plot([1],'black'), self.ax1.plot([1],'black'), self.ax1.plot([1],'black'), self.ax1.plot([1],'black'), self.ax1.plot([1],'black'), self.ax1.plot([1],'black'), self.ax1.plot([1],'black'), self.ax1.plot([1],'black')]
        
        self.ax1.grid('on')
        
        self.hdls2=[self.ax2.plot([1],'-b', alpha=0.3), self.ax2.plot([1],'-g', alpha=0.3), self.ax2.plot([1],'-r', alpha=0.3), self.ax2.plot([1],'-k', alpha=0.3)]
        self.ax2.grid('on')
        
        self.canvas.draw()
    
    
    def plotData(self, topic, title):
        
        if self.runPlotsFlag:
            
            if 'control' in str(topic): #topic != 'rtData':
                ## control plots
                msgs = self.plotMsgs[topic]
                
                data = msgs.get_data(['TS','P','I','D','C'])
                
                self.ax1.set_title(title+ ' pid')
                xs = np.arange(data.shape[0])
                
                for i in [0,1,2,3]:
                    self.hdls[i][0].set_ydata(data[:,i+1]) #skip timestemp
                    self.hdls[i][0].set_xdata(xs)
                self.ax1.set_xlim(data.shape[0]-400,data.shape[0])
                self.ax1.set_ylim(-1,1)
                self.ax1.legend(list('pidc'),loc='upper left')
                
                
                self.ax2.set_title(title)
                data = msgs.get_data(['T','N','R'])
                #cmd_data=gdata.md_hist.get_data(label+'_cmd')
                factor = [1,1,1]
                if topic == zmq_topics.topic_depth_hold_pid:
                    factor = [-1.0,-1.0,1.0] # (-) for depth
                
                if topic == zmq_topics.topic_att_hold_yaw_pid:
                    mod = [360, 360, 1]
                    for i in [0,1,2]:
                        data[:,i] = (data[:,i]%mod[i])*factor[i]
                        self.hdls2[i][0].set_ydata(data[:,i])
                        self.hdls2[i][0].set_xdata(xs)
                else:
                    for i in [0,1,2]:
                        data[:,i] = data[:,i]*factor[i]
                        self.hdls2[i][0].set_ydata(data[:,i])
                        self.hdls2[i][0].set_xdata(xs)
                    
                
                self.ax2.set_xlim(data.shape[0]-400,data.shape[0])
                min_y = data.min()
                max_y = data.max()
                self.ax2.set_ylim(min_y,max_y)
                self.ax2.legend(list('TNR'),loc='upper left')
            elif topic == 'rtData':
                msgs = self.plotMsgs[topic]
                data = msgs.get_data(['pitch','roll','yaw','depth'])
                self.ax1.set_title(title + ' attitude')
                xs = np.arange(data.shape[0])
                
                for i in [0,1,2]:
                    self.hdls[i][0].set_ydata(data[:,i]) 
                    self.hdls[i][0].set_xdata(xs)
                    
                self.hdls[3][0].set_ydata(0)
                self.hdls[3][0].set_xdata(0)
                self.ax1.set_xlim(data.shape[0]-400,data.shape[0])
                
                self.ax1.set_ylim(data.min()-5,data.max()+5)
                self.ax1.legend(list('pry'),loc='upper left')
                
                self.ax2.set_title(title + ' depth')
                #cmd_data=gdata.md_hist.get_data(label+'_cmd')
                
                data[:,3] = data[:,3]*(-1.0) ## depth (-) for depth
                
                self.hdls2[0][0].set_ydata(data[:,3])
                self.hdls2[0][0].set_xdata(xs)
                
                self.hdls2[1][0].set_ydata(0)
                self.hdls2[1][0].set_xdata(0)
                
                self.hdls2[2][0].set_ydata(0)
                self.hdls2[2][0].set_xdata(0)
    
                self.ax2.set_xlim(data.shape[0]-400,data.shape[0])
                min_y = data[:,3].min()-0.1
                max_y = data[:,3].max()+0.1
                self.ax2.set_ylim(min_y,max_y)
                self.ax2.legend(list('d'),loc='upper left')
                
                
            elif topic == 'thrusters':
                
                msgs = self.plotMsgs[topic]
                
                data = msgs.get_data(['0','1','2','3', '4', '5', '6', '7'])
                self.ax1.set_title(title)
                
                xs = np.arange(data.shape[0])
                
                for i in range(4):
                    self.hdls[i][0].set_ydata(data[:,i]) 
                    self.hdls[i][0].set_xdata(xs)
                    
                self.ax1.set_xlim(data.shape[0]-400,data.shape[0])
                
                self.ax1.set_ylim(data.min()-5,data.max()+5)
                self.ax1.legend(list('0123'),loc='upper left')
                
                #for i in range(4,8):
                if rovType == 4:
                    for i in range(4,8):
                        tt = 1
                        if (i == 4) or (i == 7):
                            tt = -1
                        self.hdls2[i-4][0].set_ydata(tt*data[:,i]) 
                        self.hdls2[i-4][0].set_xdata(xs)
                else:
                    for i in range(4,8):
                        self.hdls2[i-4][0].set_ydata(data[:,i]) 
                        self.hdls2[i-4][0].set_xdata(xs)
                    
                self.ax2.set_xlim(data.shape[0]-400,data.shape[0])
                
                self.ax2.set_ylim(data.min()-5,data.max()+5)
                self.ax2.legend(list('4567'),loc='upper left')
            
        self.canvas.draw()


    def make_widgets(self):
        propertyCol = 1
        commandCol = 3
        controlCol = 5
        
        row_index = 0
        self.create_main_col_row_labels()
       
        row_index += 1
        initRow = 6 #15
        #set video window
        col1X = 15
        row1Y = 660

        self.make_image(name='disp_image', col=1, row=row_index, x=15, y=40, char_width=968, char_height=608, update_function=self.update_image)
        self.make_image(name='disp_image_sonar', col=155, row=row_index+1, x=1250, y=660, char_width=580, char_height=350, update_function=self.update_sonar_image)


        row_index += initRow#15
        '''
        self.create_label_header(name="header", display_text1="Property", display_text2="Status",
                                 display_text3="Commands", display_text4="Control",
                                 display_text5=" Manual control ", n_col=1,
                                 n_row=row_index)
        '''
        rtDataRow = 1
        rtDataCol = 1
        cmd1Col = 3

        self.create_button("showOpenCV", "Full screen", 0, 0, self.openVideoWindow)
        self.myStyle["showOpenCV_button"].place(x=15, y=2) # put the button on the top left corner

        self.create_button("toggle", "Toggle", 0, 0, self.toggle)
        self.myStyle["toggle_button"].place(x=200, y=2) # put the button on the top left corner

        self.create_text_box(name="ROV_Data", label_text="ROV ip:", display_text="192.168.3.10", n_col=rtDataCol,  n_row=rtDataRow, textbox_width=15)
        self.myStyle["ROV_Data_label"].place(x=col1X, y=row1Y)
        self.myStyle['ROV_Data_textbox'].configure(state=DISABLED)
        
        rtDataRow += 1
        self.create_label_pair(name="rtDepth", display_text="Depth:", n_col=rtDataCol, n_row=rtDataRow)
        self.create_text_box(name="depthCmd", label_text="dDepth:", display_text="[m]", n_col=cmd1Col , n_row=rtDataRow, textbox_width=9)
        self.myStyle['depthCmd_textbox'].bind("<Key-Return>", self.updateDepth)
        rtDataRow += 1
        self.create_label_pair(name="rtPitch", display_text="Pitch:", n_col=rtDataCol, n_row=rtDataRow)
        self.create_text_box(name="pitchCmd", label_text="dPitch:", display_text="[deg]", n_col=cmd1Col, n_row=rtDataRow, textbox_width=9)
        self.myStyle['pitchCmd_textbox'].bind("<Key-Return>", self.updatePitch)
        rtDataRow += 1
        self.create_label_pair(name="rtYaw", display_text="Yaw:", n_col=rtDataCol, n_row=rtDataRow)
        self.create_text_box(name="yawCmd", label_text="dYaw:", display_text="[deg]", n_col=cmd1Col, n_row=rtDataRow, textbox_width=9)
        self.myStyle['yawCmd_textbox'].bind("<Key-Return>", self.updateYaw)
        rtDataRow += 1
        self.create_label_pair(name="rtRoll", display_text="Roll:", n_col=rtDataCol, n_row=rtDataRow)
        self.create_text_box(name="focusCmd", label_text="focusPWM:", display_text="0", n_col=cmd1Col, n_row=rtDataRow, textbox_width=9)
        self.myStyle['focusCmd_textbox'].bind("<Return>", self.updateFocus)
        rtDataRow += 1
        
        self.create_label_pair(name="rtBattery", display_text="BATT:", n_col=rtDataCol, n_row=rtDataRow)
        self.create_text_box(name="exposureCMD", label_text="exposure:", display_text="0", n_col=cmd1Col, n_row=rtDataRow, textbox_width=9)
        self.myStyle['exposureCMD_textbox'].bind("<Return>", self.updateExposure)
        #self.myStyle['focusCmd_textbox'].configure(state=DISABLED)
      
        rtDataRow += 1
        self.create_label_pair(name="rtDisk", display_text="Disk:", n_col=rtDataCol, n_row=rtDataRow)

        pidRow = 8
        pidCol = 1
        self.create_checkbox_button("showDepth", "depth control", pidCol, pidRow, self.checkDepthControl, anchor='w')
        self.myStyle["showDepth"].configure(command=self.depthSelect)
        self.create_checkbox_button("showmotors", "Trusters", pidCol+2, pidRow+1, self.checkThrusters, anchor='w')
        self.myStyle["showmotors"].configure(command=self.threustersSelect)
        pidRow += 1
        self.create_checkbox_button("showPitch", "pitch control", pidCol, pidRow, self.checkPitchControl, anchor='w')
        self.myStyle["showPitch"].configure(command=self.pitchSelect)
        pidRow += 1
        self.create_checkbox_button("showRoll", "roll control", pidCol, pidRow, self.checkRollControl, anchor='w')
        self.myStyle["showRoll"].configure(command=self.rollSelect)
        pidRow += 1
        self.create_checkbox_button("showYaw", "yaw control", pidCol, pidRow, self.checkYawControl, anchor='w')
        self.myStyle["showYaw"].configure(command=self.yawSelect)
        pidRow += 1

        modesRow = 7
        modesCol =3
        #self.create_checkbox_button("depthHold", "Depth hold", commandCol, row_index, self.checkDepthHold, anchor='w')
        #self.myStyle["depthHold"].configure(command=self.cmdDepthHold)
        self.create_button("depthHold", "Depth hold", modesCol, modesRow, self.cmdDepthHold)
        modesRow += 1
        #self.create_checkbox_button("attHold", "Attitude hold", commandCol, row_index, self.checkAttHold, anchor='w')
        #self.myStyle["attHold"].configure(command=self.dummy)
        self.create_button("attHold", "attitude hold", modesCol, modesRow, self.cmdAttHold)
        modesRow += 1
        
        row_btn_idx = 2
        btnCol = 5
        self.create_button("runRemote", "run ROV", btnCol, row_btn_idx, self.runRemote)
        row_btn_idx += 1
        self.create_button("arm", "ARM/DISARM", btnCol, row_btn_idx, self.cmdArm, tooltip="Arming motors to action...")
        row_btn_idx += 1
        self.create_button("record", "Record", btnCol, row_btn_idx, self.cmdRecord)
        row_btn_idx += 1        
        self.create_button("ledsUp", "Inc. Lights", btnCol, row_btn_idx, self.cmdIncLights)
        row_btn_idx += 1
        self.create_button("ledsDown", "Dec. Lights", btnCol, row_btn_idx, self.cmdDecLights)
        row_btn_idx += 1
        self.create_button("focusFar", "Focus far", btnCol, row_btn_idx, self.focusFar)
        row_btn_idx += 1
        self.create_button("focusNear", "Focus near", btnCol, row_btn_idx, self.focusNear)
        row_btn_idx += 1
        self.create_button("killRemote", "kill ROV", btnCol, row_btn_idx, self.killRemote)
        row_btn_idx += 1
        self.create_button("rebootRemote", "reboot ROV", btnCol, row_btn_idx, self.rebootRemote)
        
        btnCol += 2
        row_btn_idx = 6
        self.create_button("runCheckList", "Check List", btnCol, row_btn_idx, self.runCheckList)
        row_btn_idx += 1
        self.create_button("runRecords", "Run record", btnCol, row_btn_idx, self.runRecord)
        row_btn_idx += 1
        self.create_button("getRecords", "Fetch Recs", btnCol, row_btn_idx, self.fetchRecords)
        row_btn_idx += 1
        self.create_button("pausePlots", "Pause plots", btnCol, row_btn_idx, self.pausePlots)
        row_btn_idx += 1
        self.create_button("updatePIDs", "Update PID", btnCol, row_btn_idx, self.updateRovPids)
        row_btn_idx += 1
        
        btnCol +=2
        row_btn_idx = 7
        self.create_text_box(name="K", label_text="K:", display_text="", n_col=btnCol , n_row=row_btn_idx, textbox_width=9)
        row_btn_idx += 1
        self.create_text_box(name="Kp", label_text="kP:", display_text="", n_col=btnCol , n_row=row_btn_idx, textbox_width=9)
        row_btn_idx += 1
        self.create_text_box(name="Ki", label_text="kI:", display_text="", n_col=btnCol , n_row=row_btn_idx, textbox_width=9)
        row_btn_idx += 1
        self.create_text_box(name="Kd", label_text="kD:", display_text="", n_col=btnCol , n_row=row_btn_idx, textbox_width=9)
        
        
        if 0: ###
            ### show manual controls
            control_start_col = 6#12
            manualControlOffsetRow = 3
            xMiddleButton = 1007
            buttonWidth = 143
            
            self.create_control_button("yawLeft", "↙ Yaw left", control_start_col, manualControlOffsetRow, self.go_up, toolTip="yawing ROV left 5deg.")
            self.create_control_button("goLeft", "❰❰", control_start_col , manualControlOffsetRow+1, self.turn_left)
            self.create_control_button("deeper", "Deeper ⟱", control_start_col , manualControlOffsetRow+2, self.go_forwards)
            control_start_col += 1
            self.create_control_button("goForward", "⟰", control_start_col, manualControlOffsetRow, self.go_forwards)
            #self.myStyle["goForward_button"].place(x=xMiddleButton, y=732)
            self.create_control_button("stopMotion", "▄ ", control_start_col, manualControlOffsetRow+1, self.go_forwards)
            #self.myStyle["stopMotion_button"].place(x=xMiddleButton, y=767)
            self.create_control_button("goBackwords", "⟱", control_start_col, manualControlOffsetRow+2, self.go_backwards)
            #self.myStyle["goBackwords_button"].place(x=xMiddleButton, y=802)
            control_start_col += 1
            self.create_control_button("yawRight", "Yaw right ↘", control_start_col, manualControlOffsetRow, self.go_down)
            #self.myStyle["yawRight_button"].place(x=xMiddleButton+buttonWidth, y=732)
            self.create_control_button("goRight", "❱❱", control_start_col, manualControlOffsetRow+1, self.turn_right)
            #self.myStyle["goRight_button"].place(x=xMiddleButton+buttonWidth, y=767)
            self.create_control_button("shallower", "Shallower ⟰", control_start_col, manualControlOffsetRow+2, self.go_backwards)
            #self.myStyle["shallower_button"].place(x=xMiddleButton+buttonWidth, y=802)
            
            self.create_checkbox_button("inertial", "inertial movment", 8, 2, self.checkInertial, anchor='w')
            #self.myStyle["inertial"].place(x=965, y=680)
        ###############################
        
        showCamControl = True
        if showCamControl:
            ### show manual controls
            control_start_col = 10
            manualControlOffsetRow = 1
            
            self.create_control_button("autoGain", "auto gain", control_start_col , manualControlOffsetRow, self.autoGain)
            self.create_control_button("autoExp", "auto exp.", control_start_col, manualControlOffsetRow+1, self.autoExposure)
            
            self.create_control_button("incExp", "inc. Exp.", control_start_col , manualControlOffsetRow+2, self.incExp)
            self.create_control_button("decExp", "dec. Exp.", control_start_col , manualControlOffsetRow+3, self.decExp)
            #self.create_control_button("deeper", "Deeper ⟱", control_start_col , manualControlOffsetRow+2, self.go_forwards)
            
        ###############################

        self.figure1 = plt.Figure(figsize=(8,6), dpi=100)
        self.ax1 = self.figure1.add_subplot(211)
        self.ax2 = self.figure1.add_subplot(212)
        bar1 = FigureCanvasTkAgg(self.figure1, self.parent)

        self.canvas = FigureCanvasTkAgg(self.figure1, master=self.parent)
        # here: plot suff to your fig

        self.frame = Frame(self.parent)
        #frame.grid(row=0, column=9)
        toolbar = NavigationToolbar2Tk(self.canvas, self.frame)
        self.frame.place(x=1000,y=1)
        #self.canvas.get_tk_widget().grid(column=9, row=1, rowspan=1, columnspan=8)
        self.canvas.get_tk_widget().grid(rowspan=1, columnspan=8)
        self.canvas.get_tk_widget().place(x=1000,y=45)
        self.initPlots()
        self.canvas.draw()
        ###############################
 
    
    def runRecord(self):
        self.w=recRunProp(self.master)
        self.master.wait_window(self.w.top)
        
        
        recFolder = filedialog.askdirectory(initialdir = "../records", title = "Select record folder")
        if len(recFolder)> 0:
            print('Run record: %s'%recFolder)
            self.ROVHandler.rawVideo = True
            self.ROVHandler.initImgSource()
            print("%s %s %s %s"%(self.w.skipFramesVar, self.w.saveAviVar.get(), self.w.saveTiffVar.get(), self.w.freeRunVar.get() ) )
            print('cd ../scripts && ./runRec.sh %s %s %s %s %s && sleep 3'%(recFolder, str(int(self.w.skipFramesVar)),
                                                                                            self.w.saveAviVar.get(), 
                                                                                            self.w.saveTiffVar.get(),
                                                                                            self.w.freeRunVar.get() ))

            os.system('cd ../scripts && ./runRec.sh %s %s %s %s %s && sleep 3'%(recFolder, str(int(self.w.skipFramesVar)), 
                                                                                            self.w.saveAviVar.get(), 
                                                                                            self.w.saveTiffVar.get(),
                                                                                            self.w.freeRunVar.get() ))
         
    
    def runCheckList(self):
        self.w = checkListForm(self.master)
        
        self.myStyle["runCheckList_button"]['state']=DISABLED
        self.master.wait_window(self.w.top)
        self.myStyle["runCheckList_button"]['state']=NORMAL
        
        
    def fetchRecords(self):
        os.system('cd ../scripts && ./recSync.sh && sleep 3')
        
    def runRemote(self):
        os.system('cd ../scripts && ./run_remote.sh')
    
    def rebootRemote(self):
        os.system('cd ../scripts && ./reboot_remote.sh')
        
    def killRemote(self):
        os.system('cd ../scripts && ./kill_remote.sh')
    
    def pausePlots(self):
        self.runPlotsFlag = not self.runPlotsFlag
        if self.runPlotsFlag:
            self.myStyle["pausePlots_button"].config(foreground=self.myStyle['buttonFg'])
            self.myStyle["pausePlots_button"].config(activebackground=self.myStyle['activeButtonBg'])
            self.myStyle["pausePlots_button"].config(text='Pause plots')
        
        else:
            self.myStyle["pausePlots_button"].config(foreground=self.myStyle['activeDisplayButtonFg'])
            self.myStyle["pausePlots_button"].config(activebackground=self.myStyle['activeDisplayButtonBg'])
            self.myStyle["pausePlots_button"].config(text='Run plots')
        
        
    
    def updateRovPids(self):
        dkey = None
        for key in self.controllerChbx:
            if self.controllerChbx[key].get() == 0:
                if key != 'thrusters':
                    dkey = key
                    print(key)
        
        if dkey is not None:
            with open("../config_pid.json") as fid:
                data = json.load(fid)
            
            try:
                data['config_pid'][0][dkey+'_pid']['K'] = float(self.myStyle["K_textbox"].get())
                data['config_pid'][0][dkey+'_pid']['P'] = float(self.myStyle["Kp_textbox"].get())
                data['config_pid'][0][dkey+'_pid']['I'] = float(self.myStyle["Ki_textbox"].get())
                data['config_pid'][0][dkey+'_pid']['D'] = float(self.myStyle["Kd_textbox"].get())
               
                if not isSim:
                    with open("../config_pid.json", 'w') as fid:
                        json.dump(data, fid, indent=4)
                
                
                print('--update PID-->', dkey)
                msg = {'pluginUpdate':dkey, 'data':data}
                msg = pickle.dumps(msg, protocol=3)
                self.rovGuiCommandPublisher.send_multipart( [zmq_topics.topic_gui_update_pids, msg])
                
                #self.cmdDepthHold()
                #self.cmdAttHold()
                #os.system("cd ../scripts && ./updateRemotePIDs.sh")
                
            except:
                import traceback
                traceback.print_exc()
                
    def initOpencvWin(self, doInit):
        if doInit:
            cv2.namedWindow(self.cvWinName, cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty(self.cvWinName, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            self.OpencvWinInit = True
        else:
            try:
                cv2.destroyWindow(self.cvWinName)
            except:
                pass
            self.OpencvWinInit = False
    
    def openVideoWindow(self):
        self.cvWindow = not self.cvWindow
        if not self.cvWindow:
            self.initOpencvWin(False)

    def toggle(self):
        self.myStyle['disp_image'], self.myStyle['disp_image_sonar'] =self.myStyle['disp_image_sonar'], self.myStyle['disp_image']
            
    
    def fullVideoScreenEvent(self, event):
        print("fullScreen")
        self.openVideoWindow()
        
        
    def dummy(self):
        pass


    def update_button_active_command(self, button_name):
        if button_name is self.last_pressed_button:
            return
        if self.last_pressed_button in self.myStyle:
            self.myStyle[self.last_pressed_button].config(foreground=self.myStyle['buttonFg'])
            self.myStyle[self.last_pressed_button].config(activebackground=self.myStyle['activeButtonBg'])
        self.last_pressed_button = button_name
        if self.last_pressed_button in self.myStyle:
            self.myStyle[self.last_pressed_button].config(foreground=self.myStyle['activeDisplayButtonFg'])
            self.myStyle[self.last_pressed_button].config(activebackground=self.myStyle['activeDisplayButtonBg'])


if __name__=='__main__':
    try:
        root = Tk()
        #root.grid_columnconfigure(0, weight=1)
        #root.grid_rowconfigure(0, weight=1)
        #root.resizable(True, False)
        guiInstance = rovViewerWindow(root)
        root.bind("<Configure>", guiInstance.resize)

        ### placing debug - show mouse motion over GUI
        #def motion(event):
        #    x, y = event.x, event.y
        #    print('{}, {}'.format(x, y))
        #root.bind('<Motion>', motion)
        
        root.protocol("WM_DELETE_WINDOW", guiInstance.quit)
        root.mainloop()
    except:
        import traceback
        traceback.print_exc()
    finally:
        guiInstance.quit()
        if args.sim:
            os.system('tmux kill-session -t sim')
        

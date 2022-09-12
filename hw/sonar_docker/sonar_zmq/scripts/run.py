#!/usr/bin/env python
from __future__ import print_function

import roslib
roslib.load_manifest('sonar_zmq')
import sys
import rospy
import cv2
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
import zmq
import zmq_wrapper as utils
import time
import pickle



topic_stereo_camera    = b'topic_stereo_camera'
topic_stereo_camera_ts = b'topic_stereo_camera_ts'
topic_camera_port=7789


topic_sonar = b'topic_sonar'
topic_sonar_port = 9304


# socket_pub = utils.publisher(topic_camera_port)
# zmq_pub=utils.publisher(port=topic_camera_port, ip='172.17.0.4')
zmq_pub=utils.publisher(port=topic_sonar_port)



simCamState = {'expVal':-1, 'aGain':False, 'aExp':False}



class image_converter:

  def __init__(self):
    # self.image_pub = rospy.Publisher("image_topic_2",Image)

    self.bridge = CvBridge()
    self.image_sub = rospy.Subscriber("oculus/drawn_sonar",Image,self.callback)
    self.frame_cnt = 0
  def callback(self,data):
    try:
      cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
    except CvBridgeError as e:
      print(e)

    (rows,cols,channels) = cv_image.shape
    # if cols > 60 and rows > 60 :
    #   cv2.circle(cv_image, (50,50), 10, 255)

    # cv2.line(cv_image, (0,0), (cols / 2,rows / 2), (255,255,255),35)

    # cv2.imshow("Image window", cv_image)
    # cv2.waitKey(3)


    QRes = cv2.resize(cv_image, (cv_image.shape[1]//2, cv_image.shape[0]//2))


    try:
      self.frame_cnt += 1
      # self.image_pub.publish(self.bridge.cv2_to_imgmsg(cv_image, "bgr8"))
      imgl = cv_image
      # imgl = self.bridge.cv2_to_imgmsg(cv_image, "bgr8")
      # zmq_pub.send_multipart([topic_stereo_camera,pickle.dumps([ self.frame_cnt, (imgl.shape[0]*2,imgl.shape[1]*2, 3 ), time.time(), simCamState, False]),imgl.tobytes(), b''])

      # zmq_pub.send_multipart([topic_sonar,pickle.dumps([ self.frame_cnt, (imgl.shape[0],imgl.shape[1], 3 ), time.time(), simCamState, False]),imgl.tobytes(), b''])
      zmq_pub.send_multipart([topic_sonar,pickle.dumps([ self.frame_cnt, (imgl.shape[0],imgl.shape[1], 3 ), time.time(), simCamState, True]),QRes.tobytes(), imgl.tobytes()])


    except CvBridgeError as e:
      print(e)






    # try:
    #   self.image_pub.publish(self.bridge.cv2_to_imgmsg(cv_image, "bgr8"))
    # except CvBridgeError as e:
    #   print(e)


def main(args):
  ic = image_converter()
  rospy.init_node('image_converter', anonymous=True)
  try:
    rospy.spin()
  except KeyboardInterrupt:
    print("Shutting down")
  cv2.destroyAllWindows()

if __name__ == '__main__':
    main(sys.argv)
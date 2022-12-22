# Import everything needed to edit video clips
from moviepy.editor import *
 
# loading video dsa gfg intro video and getting only first 5 seconds
clip1 = VideoFileClip("camera.avi")
 
# rotating clip1 by 90 degree to get the clip2
clip2 = VideoFileClip("camera.avi")
 

 

 
 
# list of clips
clips = [clip1, clip2]
 
 
# stacking clips
final = clips_array(clips)
 
# showing final clip
final.ipython_display(width = 1080)
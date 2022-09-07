
from create_video import Topic, VideoMaker
import os


path = '/docker/bags/20220531_105553/'
csv_path = os.path.join(path, 'image_nav_bagfile_name.csv')

maker = VideoMaker(csv_path=csv_path)
maker.run()

os.system(f"""ffmpeg -n -i {os.path.join(path, 'camera.avi')} -vf "scale=w=960:h=540:force_original_aspect_ratio=1,pad=960:540:(ow-iw)/2:(oh-ih)/2" -c:v libx264 {os.path.join(path, 'camera_resized.mp4')}""")
os.system(f"""ffmpeg -n -i {os.path.join(path, 'sonar.avi')} -vf "scale=w=960:h=540:force_original_aspect_ratio=1,pad=960:540:(ow-iw)/2:(oh-ih)/2" -c:v libx264 {os.path.join(path, 'sonar_resized.mp4')}""")
os.system(f"""ffmpeg -n -i {os.path.join(path, 'camera_resized.mp4')} -i {os.path.join(path, 'sonar_resized.mp4')} -filter_complex "[0:v][1:v]hstack=inputs=2[v]" -map "[v]"  -ac 2 {os.path.join(path, 'output_video.mp4')}""")

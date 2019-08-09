import os
import pickle

if __name__=='__main__':
    devices=os.popen('find /sys/bus/usb/devices/usb*/ -name dev |grep  tty').readlines()
    dmap = {}
    for l in devices:
        dname = l.strip().split('/')[-2]
        tofind='udevadm info -q property -p %s |grep ID_SERIAL='%l.strip()[:-4]
        lname = os.popen(tofind).read().split('=')[1].strip()
        #print(dname,lname)
        if '1a86' in lname:
            dmap['ESC_USB']='/dev/'+dname
        if 'Arduino_LLC_Arduino_Leonardo' in lname:
            dmap['PERI_USB']='/dev/'+dname
        if 'CP210' in lname:
            dmap['SONAR_USB']='/dev/'+dname
        if 'FTDI' in lname:
            dmap['VNAV_USB']='/dev/'+dname
    with open('/tmp/devusbmap.pkl','wb') as fp:
        pickle.dump(dmap,fp)

else:
    if not os.path.isfile('/tmp/devusbmap.pkl'):
        print('Error cannot find /tmp/devusbmap.pkl please run detect_usb.py')
    devmap = pickle.load(open('/tmp/devusbmap.pkl','rb'))


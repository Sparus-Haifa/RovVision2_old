import time

try:
    import Jetson.GPIO as GPIO

    class LED:
        def __init__(self) -> None:
            self.light = True
            self.led_pin = 7
            GPIO.setmode(GPIO.BOARD) 
            GPIO.setup(self.led_pin, GPIO.OUT, initial=GPIO.HIGH)
            GPIO.output(self.led_pin, GPIO.HIGH)
        def toggle(self):
            if self.light is True:
                GPIO.output(self.led_pin, GPIO.LOW)
                print('low')
            else:
                GPIO.output(self.led_pin, GPIO.HIGH)
                print('high')
            self.light = not self.light

except ImportError:
    print('failed to load gpio')
    class LED:
        def toggle(self):
            print('fake blink')
            pass



class Watchdog:
    def __init__(self, topics, monitorTime = 1):
        self.tic = time.time()
        self.topics = topics
        self.monitorTime = monitorTime

        self.responding_topics = {}
        for topic in topics:
            self.responding_topics[topic]=False

        self.led = LED()

    def poke(self, topic):
        if topic not in self.responding_topics:
            return
        self.responding_topics[topic]=True

        if time.time() - self.tic >= self.monitorTime:
            if not all(self.responding_topics.values()):
                print("error")
                return

            for t in self.responding_topics:
                self.responding_topics[t]=False
            
            self.tic = time.time()

            self.led.toggle()

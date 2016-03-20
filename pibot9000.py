#!/usr/bin/env python

import RPi.GPIO as GPIO
import sys
import os
import time
import pygame
from subprocess import call
from random import *

import alsaaudio
import wave
from creds import *
import requests
import json
import re
from memcache import Client


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)


GPIO_TRIGGERC = 23
GPIO_TRIGGERL = 6
GPIO_TRIGGERR = 13
GPIO_ECHOC = 21
GPIO_ECHOL = 19
GPIO_ECHOR = 26

GPIO.setup(GPIO_TRIGGERC,GPIO.OUT)# Trigger
GPIO.setup(GPIO_TRIGGERL,GPIO.OUT)
GPIO.setup(GPIO_TRIGGERR,GPIO.OUT)
GPIO.setup(GPIO_ECHOC,GPIO.IN)      # EchoC
GPIO.setup(GPIO_ECHOL,GPIO.IN)
GPIO.setup(GPIO_ECHOR,GPIO.IN)
GPIO.setup(3,GPIO.OUT) #Left motor control
GPIO.setup(4,GPIO.OUT) #Left motor control
GPIO.setup(17,GPIO.OUT) #Right motor control
GPIO.setup(27,GPIO.OUT) #Right motor control

GPIO.setup(24,GPIO.OUT) #head light

#####################################################################################
# Set trigger to False (Low)
GPIO.output(GPIO_TRIGGERC, False)
GPIO.output(GPIO_TRIGGERL, False)
GPIO.output(GPIO_TRIGGERR, False)

# Allow module to settle
time.sleep(0.5)

def sonarC(n):
        # Send 10us pulse to trigger
        GPIO.output(GPIO_TRIGGERC, True)
        time.sleep(0.00001)
        GPIO.output(GPIO_TRIGGERC, False)

        startC = time.time()

       # this doesn't allow for timeouts !

        while GPIO.input(GPIO_ECHOC)==0:
                startC = time.time()

        while GPIO.input(GPIO_ECHOC)==1:
                stopC = time.time()

        # Calculate pulse length
        elapsedC = stopC-startC

        # Distance pulse travelled in that time is time
        # multiplied by the speed of sound (cm/s)
        distanceC = elapsedC * 34000

        # That was the distance there and back so halve the value
        distanceC = distanceC / 2

        return distanceC

##################################################################################################
def sonarR(n):
        # Send 10us pulse to trigger
        GPIO.output(GPIO_TRIGGERR, True)
        time.sleep(0.00001)
        GPIO.output(GPIO_TRIGGERR, False)
        
        startR = time.time()

       # this doesn't allow for timeouts !

        while GPIO.input(GPIO_ECHOR)==0:
                startR = time.time()

        while GPIO.input(GPIO_ECHOR)==1:
                stopR = time.time()

        # Calculate pulse length
        elapsedR = stopR-startR

        # Distance pulse travelled in that time is time
        # multiplied by the speed of sound (cm/s)
        distanceR = elapsedR * 34000

        # That was the distance there and back so halve the value
        distanceR = distanceR / 2

        return distanceR

###################################################################################################
def sonarL(n):
        # Send 10us pulse to trigger
        GPIO.output(GPIO_TRIGGERL, True)
        time.sleep(0.00001)
        GPIO.output(GPIO_TRIGGERL, False)
        
        startL = time.time()

       # this doesn't allow for timeouts !

        while GPIO.input(GPIO_ECHOL)==0:
                startL = time.time()

        while GPIO.input(GPIO_ECHOL)==1:
                stopL = time.time()

        # Calculate pulse length
        elapsedL = stopL-startL

        # Distance pulse travelled in that time is time
        # multiplied by the speed of sound (cm/s)
        distanceL = elapsedL * 34000

        # That was the distance there and back so halve the value
        distanceL = distanceL / 2

        return distanceL

#########################################################################################

#motor defs

def stop():
    GPIO.output(3,0) 
    GPIO.output(4,0)
    GPIO.output(17,0)
    GPIO.output(27,0)

def forward():
   # print "forward"
    GPIO.output(3,0)
    GPIO.output(4,1)
    GPIO.output(17,0)
    GPIO.output(27,1)

def rev():
  #  print "rev"
    GPIO.output(3,1)
    GPIO.output(4,0)
    GPIO.output(17,1)
    GPIO.output(27,0)

def left():
  #  print "left"
    GPIO.output(3,0)
    GPIO.output(4,1)
    GPIO.output(17,1)
    GPIO.output(27,0)

def right():
    #print "right"
    GPIO.output(3,1)
    GPIO.output(4,0)
    GPIO.output(17,0)
    GPIO.output(27,1)



def hon():
    print "light on"
    GPIO.output(24,1)
    time.sleep(.5)

def hoff():
    print "light off"
    GPIO.output(24,0)
    time.sleep(.5)


pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.init()
roar = pygame.mixer.Sound(os.path.join('data','trex.ogg'))
r2d2 = pygame.mixer.Sound(os.path.join('data','r2d2.ogg'))
danger = pygame.mixer.Sound(os.path.join('data','danger.ogg'))
back = pygame.mixer.Sound(os.path.join('data','back.ogg'))
learn = pygame.mixer.Sound(os.path.join('data','learn.ogg'))
pygame.mixer.music.load(os.path.join('data', 'iron.ogg'))

done = False
auto = False
hlight = False
main = False
# Initialize the joysticks
pygame.joystick.init()

#############################################################
#alexa
############################################################
button = 18 #GPIO Pin with button connected
lights = [9, 11] # GPIO Pins with LED's conneted
device = "plughw:1" # Name of your microphone/soundcard in arecord -L

#Setup
recorded = False
servers = ["127.0.0.1:11211"]
mc = Client(servers, debug=1)
path = os.path.realpath(__file__).rstrip(os.path.basename(__file__))



def internet_on():
    try:
        r =requests.get('https://api.amazon.com/auth/o2/token')
        print "Connection OK"
        return True
    except:
        print "Connection Failed"
        return False

    
def gettoken():
    token = mc.get("access_token")
    refresh = refresh_token
    if token:
        return token
    elif refresh:
        payload = {"client_id" : Client_ID, "client_secret" : Client_Secret, "refresh_token" : refresh, "grant_type" : "refresh_token", }
        url = "https://api.amazon.com/auth/o2/token"
        r = requests.post(url, data = payload)
        resp = json.loads(r.text)
        mc.set("access_token", resp['access_token'], 3570)
        return resp['access_token']
    else:
        return False
        

def alexa():
    url = 'https://access-alexa-na.amazon.com/v1/avs/speechrecognizer/recognize'
    headers = {'Authorization' : 'Bearer %s' % gettoken()}
    d = {
        "messageHeader": {
            "deviceContext": [
                {
                    "name": "playbackState",
                    "namespace": "AudioPlayer",
                    "payload": {
                        "streamId": "",
                        "offsetInMilliseconds": "0",
                        "playerActivity": "IDLE"
                    }
                }
            ]
        },
        "messageBody": {
            "profile": "alexa-close-talk",
            "locale": "en-us",
            "format": "audio/L16; rate=16000; channels=1"
        }
    }
    with open(path+'recording.wav') as inf:
        files = [
                ('file', ('request', json.dumps(d), 'application/json; charset=UTF-8')),
                ('file', ('audio', inf, 'audio/L16; rate=16000; channels=1'))
                ]   
        r = requests.post(url, headers=headers, files=files)
    if r.status_code == 200:
        for v in r.headers['content-type'].split(";"):
            if re.match('.*boundary.*', v):
                boundary =  v.split("=")[1]
        data = r.content.split(boundary)
        for d in data:
            if (len(d) >= 1024):
                audio = d.split('\r\n\r\n')[1].rstrip('--')
        with open(path+"response.mp3", 'wb') as f:
            f.write(audio)
        os.system('mpg123 -q {}1sec.mp3 {}response.mp3'.format(path, path))
    else:

        for x in range(0, 3):
            time.sleep(.2)
        
            time.sleep(.2)
        


            
def start():
        alexaon = True
        last = 1
        while alexaon==True:
                
                for event in pygame.event.get(): # User did something
                    if event.type == pygame.QUIT: # If user clicked close
                        done=True # Flag that we are done so we exit this loop
                                
                                # Possible joystick actions: JOYAXISMOTION JOYBALLMOTION JOYBUTTONDOWN JOYBUTTONUP JOYHATMOTION
                                

                            # Get count of joysticks
                joystick_count = pygame.joystick.get_count()

                            # For each joystick:
                for i in range(joystick_count):
                    joystick = pygame.joystick.Joystick(i)
                    joystick.init()
                val = 1
                if (joystick.get_button(1) == True):
                        val = 0
                if val != last:
                        last = val
                        if val == 1 and recorded == True:
                                rf = open(path+'recording.wav', 'w') 
                                rf.write(audio)
                                rf.close()
                                inp = None
                                alexa()
                        elif val == 0:
                                inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, device)
                                inp.setchannels(1)
                                inp.setrate(16000)
                                inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
                                inp.setperiodsize(500)
                                audio = ""
                                l, data = inp.read()
                                if l:
                                        audio += data
                                recorded = True
                elif val == 0:
                        l, data = inp.read()
                        if l:
                                audio += data
                elif (joystick.get_hat(0) == (0,-1)):
                        alexaon = False
                time.sleep(.01)

        
        
def alexastart():
        if __name__ == "__main__":
            while internet_on() == False:
                print "."
            token = gettoken()
            os.system('mpg123 -q {}1sec.mp3 {}hello.mp3'.format(path, path))
            start()

    
#############################################################
#joystick
#############################################################


def joy():
        
        while internet_on() == False:
                print "."
        token = gettoken()
        os.system('mpg123 -q {}1sec.mp3 {}hello.mp3'.format(path, path))
        for x in range(0, 3):
                time.sleep(.1)
                time.sleep(.1)

        last = 1
        hlight = False
        done = False
        while done==False:
                
            # EVENT PROCESSING STEP
                for event in pygame.event.get(): # User did something
                    if event.type == pygame.QUIT: # If user clicked close
                        done=True # Flag that we are done so we exit this loop
                                
                                # Possible joystick actions: JOYAXISMOTION JOYBALLMOTION JOYBUTTONDOWN JOYBUTTONUP JOYHATMOTION
                                

                            # Get count of joysticks
                joystick_count = pygame.joystick.get_count()

                            # For each joystick:
                for i in range(joystick_count):
                    joystick = pygame.joystick.Joystick(i)
                    joystick.init()



                
                val = 1
                if (joystick.get_button(1) == True): #B
                        val = 0
                if val != last:
                        last = val
                        if val == 1 and recorded == True:
                                rf = open(path+'recording.wav', 'w') 
                                rf.write(audio)
                                rf.close()
                                inp = None
                                alexa()
                        elif val == 0:
                                inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, device)
                                inp.setchannels(1)
                                inp.setrate(16000)
                                inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
                                inp.setperiodsize(500)
                                audio = ""
                                l, data = inp.read()
                                if l:
                                        audio += data
                                recorded = True
                elif val == 0:
                        l, data = inp.read()
                        if l:
                                audio += data

                elif(joystick.get_axis(1) < -0.5): #Forward
                        forward()          
                elif (joystick.get_axis(1) > 0.5): #backward
                        rev()
                elif (joystick.get_axis(0) < -0.5): #Left
                        left()
                elif (joystick.get_axis(0) > 0.5): #Right
                        right()
##                elif (joystick.get_button(1) == True): #B
##                       roar.play()
                elif (joystick.get_button(3) == True): #X
                        r2d2.play()
                elif (joystick.get_button(0) == True): #A
                        auto1()
                elif (joystick.get_button(4) == True): #Y
                        learn.play()
                elif (joystick.get_hat(0) == (0,1)): #D-PAD UP
                        back.play()
                elif (joystick.get_hat(0) == (-1,0)): #D-PAD LEFT
                        pygame.mixer.music.play() 
                elif (joystick.get_hat(0) == (1,0)): #D-PAD RIGHT
                        pygame.mixer.music.stop()
                elif (joystick.get_hat(0) == (0,-1)): #D-PAD DOWN
                        hoff()
                        done=True
                elif (joystick.get_button(7) == True): #R1
                        roar.play()
                elif (joystick.get_button(6) == True): #L1
                        danger.play()
                
                elif (joystick.get_button(11) == True) and hlight == False: #start
                            hon()
                            hlight=True
                elif (joystick.get_button(11) == True) and hlight == True:
                            hoff()
                            hlight=False

                else:
                        stop()
                        time.sleep(0.01)

################################################################
    #auto
################################################################
def auto1():
        auto = True
        while auto==True:
                for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                                done=True
                joystick_count = pygame.joystick.get_count()
                for i in range(joystick_count):
                        joystick = pygame.joystick.Joystick(i)
                        joystick.init()
                forward()
                time.sleep(0.3)

                ran = randint(1, 3)
                center = sonarC (0)
                lefty = sonarL (0)
                righty = sonarR (0)


                if (center < 60) and (lefty < 60) and (righty < 60):
                        
                        print"all"
                        rev()
                        time.sleep(ran)
                        right()
                        time.sleep(ran)
                        # forwards again
                        forward()


                elif (center < 50) and (lefty < 50):
                        
                        print"left and center"
                        right()
                        time.sleep(0.5)
                        # forwards again
                        forward()


                elif (center < 50) and (righty < 50):
                        
                        print"right and center"
                        left()
                        time.sleep(0.5)
                        # forwards again
                        forward()

                elif (righty < 50):
                        
                        print"right"
                        left()
                        time.sleep(0.25)
                        # forwards again
                        forward()

                elif (lefty < 50):
                        
                        print"left"
                        right()
                        time.sleep(0.25)
                        # forwards again
                        forward()

                elif (center < 60):
                       
                        print"center"
                        rev()
                        time.sleep(ran)
                        right()
                        time.sleep(ran)
                        # forwards again
                        forward()

                elif (lefty < 50) and (righty < 50):
                        
                        print"left and right"
                        rev()
                        time.sleep(ran)
                        right()
                        time.sleep(ran)
                        # forwards again
                        forward()

                elif (joystick.get_button(10) == True): #select
                        if (auto == True):
                                done=False
                                auto=False
                                print"auto off"
                                time.sleep(.5)
                elif (joystick.get_hat(0) == (0,-1)):
                        hoff()
                        stop()
                        auto=False
                        time.sleep(3)
                else:
                        if (auto == True):
                                forward()

while main==False:
        for event in pygame.event.get():
                if event.type == pygame.QUIT:
                        done=True
        joystick_count = pygame.joystick.get_count()
        for i in range(joystick_count):
                joystick = pygame.joystick.Joystick(i)
                joystick.init()
        print"<----------Pibot9000 control interface---------->"
        print"Press button A for Auto"
        print"Press button B for joystick, Auto and Alexa"
        print"Press button Y for just Alexa"
        if (joystick.get_button(0) == True):
                print"-----AUTO-----"
                time.sleep(1)
                auto1()
        elif (joystick.get_button(1) == True):
                print"-----JOYSTICK-----"
                time.sleep(1)
                joy()
        elif (joystick.get_hat(0) == (0,-1)):
                hoff()
                print"Goodbye"
                time.sleep(1)
                main=True
        elif (joystick.get_button(4) == True):
                print"-----ALEXA-----"
                alexastart()
        elif (auto == False):
                stop()
                
        pygame.event.wait()
        


# Use Ctrl+C to quit.
# If you forget this line, the program will 'hang'
# on exit if running from IDLE.

pygame.quit ()

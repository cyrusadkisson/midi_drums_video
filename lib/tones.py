import mido
import os
import xml.etree.ElementTree as ET
import sys
import datetime
from decimal import Decimal
from processing_py import *
from pprint import pprint
import subprocess
from random import randint
import time
from PIL import ImageColor
import shutil
import re


basedir = os.path.dirname(os.path.realpath(__file__))
logFile = basedir+"/../log/processing.log"
debug = False
DEFAULT_TEMPO = 500000
TEMPO = 48200
TICK = 480


class tones:
    def __init__(self, config, app):
        self.config = config
        self.duration = 0
        self.dialogs = []
        self.bmpMatrix = {}
        self.app = app
        self.tmpDir = "{0}{1}".format(
            self.config['general']['tmpDir'], time.time())
        os.makedirs(self.tmpDir, exist_ok=True)
        self.timerMatrix = []

        self.ffmpeg = config['general']['ffmpeg']
        self.ffprobe = config['general']['ffprobe']
        self.fps = config['video']['fps']
        # ffmpeg log level ( error, warning, info, debug, etc)
        self.logLevel = config['general']['ffmpegLogLevel']
        self.filesForRemove = []
        self.emptyBackgroundFilename = self.tmpDir+"/background.png"
        self.start = 0

    def read_tones(self, orig_midi, midi_no):

        midfile = mido.MidiFile(orig_midi)

        self.writeLog("Info: Midi Information: {}".format(orig_midi))
        self.writeLog("Info: Ticks per beat: {}".format(
            midfile.ticks_per_beat))
        self.writeLog("Info: Total tracks: {}".format(len(midfile.tracks)))
        self.writeLog("Info: Midi Type: {}".format(midfile.type))


        noteTimer = {}
        #layer = 1
        ticks_per_beat = int(midfile.ticks_per_beat)

        for idx, track in enumerate(midfile.tracks):
            #layer += 1
            #layer = int(midi_no)*100 + layer % 100
#
#       <Region name="dusty-t0-1-1.1" muted="0" opaque="1" locked="0" video-locked="0" automatic="0" whole-file="0" 
#       import="0" external="1" sync-marked="0" left-of-split="0" right-of-split="0" hidden="0" position-locked="0" 
#       valid-transients="0" start="86748" length="15423669" position="0" beat="0" sync-position="0" ancestral-start="0" 
#       ancestral-length="0" stretch="1" shift="1" positional-lock-style="MusicTime" layering-index="0" tags="" contents="0" 
#       start-beats="3.9759539759539764" length-beats="706.91886941886935" id="93756" type="midi" first-edit="nothing" source-0="93562" master-source-0="93562"/>            
            tempo = DEFAULT_TEMPO
            
            bpm = float(self.getBmpByTime(0.0))
            tempo = mido.bpm2tempo(bpm)  
                      
            deltaStart=int(self.start)/TEMPO
            #mido.tick2second(int(self.start),
            #                                  ticks_per_beat, DEFAULT_TEMPO)
            
            timer=0        
            lastNoteTimer=0
            self.duration=0
            for msg in track:
                if debug:
                    self.writeLog(str(msg))

                bpm = float(self.getBmpByTime(timer))
                tempo = mido.bpm2tempo(bpm)

                timer += mido.tick2second(msg.time,
                                              ticks_per_beat, tempo)

                timerRight=timer-deltaStart
                
                if msg.type == 'note_on':
                    
                    noteTimer[msg.note] = {}
                    noteTimer[msg.note]['start'] = timerRight

                #print( "timer:")
                #pprint (timer)
                #print( "timerRight:")
                #pprint (timerRight)                
                #print ( "note")
                #pprint( msg )

                if msg.type == 'note_off':
                    note = msg.note
                    try:
                        if not self.config['note'][str(msg.note)]:
                            self.writeLog(
                                "Warning: note {} do not described in config.json file. Will use default note 35.".format(msg.note))
                            note = "35"
                    except:
                        self.writeLog(
                            "Warning: note {} do not described in config.json file. Will use default note 35.".format(msg.note))
                        note = "35"

                    noteTimer[msg.note]['end'] = timerRight
                    noteTimer[msg.note]['posX'] = self.config['note'][str(
                        note)]['posX']
                    noteTimer[msg.note]['posY'] = self.config['note'][str(
                        note)]['posY']
                    noteTimer[msg.note]['extent'] = self.config['note'][str(
                        note)]['extent']
                    noteTimer[msg.note]['color'] = self.config['note'][str(
                        note)]['color']
                    self.timerMatrix.append(noteTimer[msg.note])
                    lastNoteTimer=timerRight

        if lastNoteTimer > self.duration:
            self.duration = lastNoteTimer+5
        return True

    def saveEmptyBackground(self):
        try:
            self.app.background(0, 0, 0)
            self.app.save('"'+self.emptyBackgroundFilename+'"')  # save
            time.sleep(1)
        except Exception as e:
            self.writeLog("Error: Something wrong. Cannot save background empty image {}. Exception :{} ".format(
                self.emptyBackgroundFilename, e))
            return False

        return True

    def drawCircles(self):
        # try:
        count = 0
        timer = 0.0
        while(timer < self.duration):
            try:
                notes = self.getNotesByTime(timer)
                fileName = self.tmpDir+"/image"+str("%.5d" % count) + ".png"
                count = count+1
                timer = timer+1/self.config['video']['fps']
                #print("Make image for time :"+str(timer))
                if not notes:  # we copy black image if haven't notes. Draw only notes exists
                    shutil.copyfile(self.emptyBackgroundFilename, fileName)
                    continue

                self.app.background(0, 0, 0)
                for note in notes:
                    (r, g, b) = ImageColor.getcolor(note['color'], "RGB")
                    self.app.fill(r, g, b)
                    self.app.noStroke()
                    self.app.circle(note['posX'], note['posY'], note['extent'])
                self.app.save('"'+fileName+'"')  # save
            except Exception as e:
                self.writeLog(
                    "Error: Something wrong. Cannot save frame note for time: {}. Exception :{} ".format(timer, e))
                return False

        return True

    def ffmpegPrepareCommand(self, outputFileName):
        cmd = "{} -y -loglevel {} -r {} -i {}  -c:v libx264 -vf fps={} -pix_fmt yuv420p {}".format(
            self.ffmpeg,
            self.logLevel,
            self.fps,
            self.tmpDir+"/image%5d.png",
            self.fps,
            outputFileName
        )
        return cmd

    def getNotesByTime(self, timer):
        notes = []
        for t in self.timerMatrix:
            if timer >= t['start'] and timer <= t['end']:
                notes.append(t)
        return notes

    def writeLog(self, message):
        today = datetime.datetime.today()
        dt = today.strftime('%Y-%m-%d %H:%M:%S')
        sys.stderr.write(dt+" "+message+"\n")
        try:
            with open(logFile, "a") as file_object:
                file_object.write(dt+" "+message+"\n")
        except:
            sys.stderr.write(dt+" "+logFile+"\n")
            return False

    def getTempo(self, ardour_file):
        try:
            tree = ET.parse(ardour_file)
            root = tree.getroot()
            for tempomap in tree.iter('TempoMap'):
                for tempo in tempomap.iter('Tempo'):

                    frame = tempo.get('frame')
                    startbpm = tempo.get('beats-per-minute')
                    endbpm = tempo.get('end-beats-per-minute')
                    movable = tempo.get('movable')
                    timer = int(frame)/TEMPO
                    self.bmpMatrix[timer] = {}
                    self.bmpMatrix[timer]['startbpm'] = startbpm
                    self.bmpMatrix[timer]['endbpm'] = endbpm
                    self.bmpMatrix[timer]['timer'] = timer
                    self.bmpMatrix[timer]['movable'] = movable
            if not self.duration:
                self.writeLog("Error: Do not get duration of midi")
                return False

            #pprint("bmpMatrix:")
            #pprint(self.bmpMatrix)
        except Exception as e:
            self.writeLog("Error: Something wrong. Exception :{} ".format(e))
            return False
        return True

    def getBmpByTime(self, timer):
        getNext = True
        for keyTimer in self.bmpMatrix:
            #pprint(timer)
            #pprint("timer")

            if timer >= keyTimer:
                startbpm = float(self.bmpMatrix[keyTimer]['startbpm'])
                endbpm = float(self.bmpMatrix[keyTimer]['endbpm'])
                movable = int(self.bmpMatrix[keyTimer]['movable'])
                timerFrames = float(keyTimer)
                getNext = True
                nextKeyTimer = timerFrames
                continue
            if getNext:
                nextKeyTimer = float(keyTimer)
                getNext = False

        if 1 == movable:
            #pprint(startbpm)
            #pprint("nextKeyTimer")
            #pprint(nextKeyTimer)
            #pprint("timerFrames")
            #pprint(timerFrames)
            #pprint("Movable")
            #pprint(movable)
            #pprint("startbpm")
            #pprint(startbpm)
            #pprint("endbpm")
            #pprint(endbpm)
            if nextKeyTimer != timerFrames:
                bmp = startbpm+(endbpm-startbpm) * \
                    (timer-timerFrames)/(nextKeyTimer-timerFrames)

            else:
                bmp = endbpm
        else:
            bmp = startbpm
        return bmp

    def doExec(self, cmd):
        try:
            result = subprocess.run(cmd, shell=True)
        except subprocess.CalledProcessError:
            # print "error code", grepexc.returncode, grepexc.output
            self.writeLog("Error: Someting wrong during execute command "+cmd)
            return False
        if result.returncode == 0:
            return True
        return False

    def getTmpFileName(self, suffix):
        # succeeds even if directory exists.
        os.makedirs(self.tmpDir, exist_ok=True)
        fileName = "{0}/{1}{2}{3}".format(self.tmpDir,
                                          time.time(), randint(10000, 99999), suffix)
        self.filesForRemove.append(fileName)
        return(fileName)

    def removeTmpFiles(self):
        for file in self.filesForRemove:
            if os.path.exists(file):
                os.remove(file)
                self.writeLog("Temp file "+file + " was removed")
        shutil.rmtree(self.tmpDir, True)
        return True

    def getDuration(self, root):

        for locations in root.iter('Locations'):
            for location in locations.iter('Location'):
                end = float(location.get('end')) / TEMPO

        if end > self.duration:
            self.duration = end

        return self.duration

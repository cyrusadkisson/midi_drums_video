import argparse
import mido
import os
import xml.etree.ElementTree as ET
import re
import sys
from lib.tones import tones
from lib.version import version
import json
import unicodedata
from processing_py import *
import shutil


DEFAULT_TEMPO = 500000
baseDir = os.path.dirname(os.path.realpath(__file__))
type_help = "Pass '--help' to show the help message."


def find_midis(root_xml, root_dir):
    disk_midis = dict()
    sources = dict()

    for source in root_xml.findall(".//Sources/Source"):
        if not source.attrib['type'] == 'midi':
            continue

        source_id = source.attrib.get('id')
        source_name = source.attrib.get('name')
        sources[source_id] = source_name

    for r, dirs, files in os.walk(os.path.join(root_dir, 'interchange')):
        for file in files:
            fn, ext = os.path.splitext(file)
            if not ext == '.mid':
                continue

            for source_k in sources.keys():
                if sources[source_k] == file:
                    sources[source_k] = os.path.join(r, file)
                    break
    return sources


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=str,
                        help='The directory where the .ardour file is locatedF')
    parser.add_argument('-c', '--config', required=False,
                        help='Path to config file')
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s '+version)
    parser.add_argument('--output', type=str,
                        help='The output video file. Must have mp4 extension, eg video.mp4')

    args = parser.parse_args()

    if not args.directory or not os.path.exists(args.directory):
        sys.stderr.write(
            "Error: Please supply a valid 'directory'. {}".format(type_help))
        sys.exit(1)

    configFile = args.config

    if args.config is None:
        configFile = baseDir+"/data/config.json"     # Config
    else:
        configFile = str(args.threads)

    with open(configFile) as json_file:
        config = json.load(json_file)

    if  args.output is None:
        outputFileName = os.path.normpath(args.directory+"/export/" +
                                      os.path.basename(args.directory.rstrip('/')) + ".mp4")    
    else: 
        if args.output.endswith('.mp4'):
            outputFileName=args.output
        else: 
            print( "Error: output file must have the mp4 extension, eg /path/video.mp4")
            sys.exit(1)

    app = App(config['video']['width'], config['video']
              ['height'])  # create window: width, height

    tones = tones(config, app )
    #tones.app=app

    ardour_file = None

    tones.writeLog("Info: Looking for '.ardour' in {}".format(args.directory))
    for _file in os.listdir(args.directory):
        if _file.endswith(".ardour"):
            ardour_file = os.path.join(args.directory, _file)
            tones.writeLog("Found: {}\n".format(ardour_file))
            tones.writeLog("="*40)

            break

    if not ardour_file:
        tones.writeLog("Error: No '.ardour' file found in {}".format(
            os.path.abspath(args.directory)))
        app.exit()

    regex = re.compile(r"{}".format('drums'))
    root = ET.parse(ardour_file)


    source_0s = dict()

    tones.writeLog("Info: Looking up routes...")
    routes = list(root.findall('.//Routes/Route'))
    for route in routes:
        # How to make decisions based on attributes even in 2.6:
        route_name = route.attrib.get('name')
        match = regex.search(route_name)

        if not match:
            continue

        tones.writeLog(
            "Info: Yes! A route with name '{}' matched 'drums' ".format(route_name))
        midi_id = route.attrib.get("midi-playlist")

        tones.writeLog("Info: Looking up playlists...")
        for playlist in root.findall('.//Playlists/Playlist'):
            if not playlist.attrib.get("id") == midi_id:
                continue

            tones.writeLog("Info: Yes! Playlist(name={},id={}) matched <midi_id>='{}'".format(
                playlist.attrib.get("name"), playlist.attrib.get("id"), midi_id))

            tones.writeLog("Info: Looking up regions...")
            for region in playlist:
                if not region.tag == 'Region':
                    continue

                source_0 = region.attrib.get('source-0')
                if not source_0:
                    tones.writeLog(
                        "Warning: source-0 has no valid value in <Playlist><Region>..</Region></Playlist>. Skipping...")
                    continue
                source_0s[route_name.strip()] = source_0

                start = region.attrib.get('start')
                if not start:
                    tones.writeLog(
                        "Warning: Cannot get start value")                    
                    tones.start=0
                else: 
                    tones.start=start
                                    
                break

        
        

    if not source_0s:
        tones.writeLog(
            "Error: Did not find any 'midi' file to process!\nEither one of (Route/Playlist/Region) is missing.")
        app.exit()

    tones.writeLog("Info: Looking up midi files in local disk.")

    midis = find_midis(root, args.directory)
    tones.writeLog("Info: Found a total of {} midi files.".format(len(midis)))
    tones.writeLog("="*40)
    total_processed = 0

    for route_name in source_0s.keys():
        source0_id = source_0s[route_name]

        tones.writeLog("Info: Processing for drums")

        tones.writeLog(
            "Info: Route 'name': drums matched")

        midi_file = midis[source0_id]

        if not midi_file or not os.path.exists(midi_file):
            tones.writeLog(
                "Warning: Cannot find the file source:0:{}, filename: {}! Skipping...".format(source_0, midi_file))
            continue

        tones.writeLog("Processing name:'{}', source-0{},\n\tmidifile: {}".format(
            route_name, source0_id, midi_file))

        tones.writeLog("Info: Looking up duration...")
        tones.getDuration(root)
        tones.getTempo(ardour_file)        

        tones.writeLog("Info: Duration is :{}".format(tones.duration))

        if not tones.read_tones(midi_file, total_processed):  # prepare ass file
            tones.writeLog(
                "Error: Cannot prepare subtitles file for source:0:{}, filename: {}! Skipping...".format(source_0, midi_file))
            continue

        total_processed = total_processed + 1
        tones.writeLog(
            "Info: all notes are read")
        tones.writeLog("="*40)
        tones.writeLog(
            "Info: Start preparing images")

    tones.saveEmptyBackground()
    tones.drawCircles()

    tmpOutputFileName = os.path.normpath(tones.getTmpFileName(".mp4"))
    #outputFileName = os.path.normpath(args.directory+"/export/" +
    #                                  os.path.basename(args.directory.rstrip('/')) + ".mp4")
    tones.writeLog("Info: duration: "+str(tones.duration))
#
    cmd = tones.ffmpegPrepareCommand(tmpOutputFileName)
    tones.writeLog("Info: Execute command: {}".format(cmd))
    if tones.doExec(cmd):
        tones.writeLog(
            "Info: Processing finished for for source:0:{}, filename: {}...".format(source_0, midi_file))

        os.makedirs(args.directory+"/export", exist_ok=True)

        try:
            shutil.copy(tmpOutputFileName, outputFileName)
            tones.writeLog(
                "Info: Processed video file is stored to "+outputFileName)
        except Exception as e:
            tones.writeLog(
                "Warning: cannot copy output file {} to {}. Processed video file is stored to {}. Exception: {}".format(tmpOutputFileName, outputFileName, tmpOutputFileName, e))
            app.exit()
            sys.exit(1)

    else:
        tones.writeLog("Error: error while executing command: "+cmd)
        tones.removeTmpFiles()
        app.exit()
        sys.exit(1)
            
    tones.writeLog(
        "Info: Total # of midis processed: {}".format(total_processed))
    tones.writeLog(
        "Info: processing finished")
    tones.writeLog(
        "")
    tones.removeTmpFiles()
    app.exit()

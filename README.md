"# midi_drums_video" 

##  What is it?
##  -----------
The script will check the midi drums in the specified directory, generate a video with white circles at the moments of the beats, the size and location of the circles depend on the notes.

- [Description](#description)
- [Required soft](#required-soft)
- [Whats new](#whats-new)
- [How to install](#how-to-install)
- [How to run](#how-to-run)
- [Config file example](#config-file-example)

## Description
The script will check the midi drums in the specified directory, generate a video with white circles at the moments of the beats, the size and location of the circles depend on the notes. If there exists more than one drums midi, then all of such midi will be shown on the video.
Each note have description in `data/config.json` file and you can define the size, position, color of circles, outline, shadow. Also, in `data/config.json` you can define output video size and fps.
All information messages are logging into `log/processing.log` file. 
Output video file will be stored into /somedirectory/`session-name`/export/`session-name.mp4`.

## Required soft

  + python 3.6 and above
  + ffmpeg 4 and above
  + processing.py


##  Whats new

  version 2.1.9 20210131

  + Fixed search for drums midi files


  version 2.1.8 20210131

  + Added noStroke for circles
  

  version 2.1.6 20210131

  + Added --output option 


  version 2.1.5 20210131

  + Fixed minor errors
  + Fixed duration of video to last note +5 sec


  version 2.1.1 20210131

  + Fixed many time sync and bpm errors


  version 2.1.0 20210131

  + Working version with `processing_py`


  version 2.0.0 20210126

  + Transition version from subtitles to processing.py


  version 1.0.2 20210119

  + Fixed ffmpeg installation docs
  + Fixed list of imported modules


  version 1.0.1 20210119

  + Added documentation



##  How to install
For Ubuntu ( or any Debian distributive):
```bash
sudo apt-get -y install fontconfig fonts-roboto 

#You can use default ffmpeg ( if it version is 4 ), or install static ffmpeg from [FFmpeg Static Builds](https://johnvansickle.com/ffmpeg/)
#Download ffmpeg 4.3.1 ( or above ) for your system. For x86 plese download `amd64`.

wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar xf ffmpeg-release-amd64-static.tar.xz
sudo mkdir /usr/share/ffmpeg
sudo mv ffmpeg-4.3.1-amd64-static/ /usr/share/ffmpeg
sudo ln -s /usr/share/ffmpeg/ffmpeg-4.3.1-amd64-static/ffmpeg /usr/bin/ffmpeg
sudo ln -s /usr/share/ffmpeg/ffmpeg-4.3.1-amd64-static/ffprobe /usr/bin/ffprobe

pip3 install mido
pip3 install processing-py --upgrade
git clone https://github.com/ikorolev72/midi_drums_video.git
cd midi_drums_video
./drumsvideo.py --help
```



## How to run

```
usage: drumsvideo.py [-h] [--directory DIRECTORY] [-c CONFIG] [-v]

optional arguments:
  -h, --help            show this help message and exit
  --directory DIRECTORY
                        The directory where the .ardour file is locatedF
  -c CONFIG, --config CONFIG
                        Path to config file
  -v, --version         show program's version number and exit
```




# Appendix

### Config file example
```json

{
  "general": {
    "ffmpeg": "ffmpeg", // path to ffmpeg , eg /usr/bin/ffmpeg
    "ffprobe": "ffprobe",
    "ffmpegLogLevel": "info", // log level, eg warning, error, info, debug
    "tmpDir": "tmp"
  },
  "video": {
    "width": 1920, // output video resolution
    "height": 1080,
    "fps":30 // frame per second in output video
  },
  "note": { // notes description
    "35": {
      "posX": 897, // position X
      "posY": 21,  // position y
      "extent": 225, // circle size
      "color": "#FFFFFF"  // color of circles in HTML format
    },
    "36": {
      ...
```




##  Bugs
##  ------------




  Licensing
  ---------
	GNU

  Contacts
  --------

     o korolev-ia [at] yandex.ru
     o http://www.unixpin.com

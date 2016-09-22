from celery import Celery
from pymediainfo import MediaInfo
import pafy
import os
import shutil
from shutil import copyfile
import subprocess
import configparser
import zipfile
import jsonpickle
import requests
from xml.dom import minidom

# New celery worker connected to default RabbitMQ
app = Celery('worker')
app.config_from_object('celeryconfig')
FNULL = open(os.devnull, 'w')
HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'

@app.task
def get_settings(file_settings):
    settings = configparser.ConfigParser()
    settings.read(file_settings)
    return settings

@app.task
def get_video_size(input_file):
    media_info = MediaInfo.parse(input_file)
    for track in media_info.tracks:
        if track.track_type == 'Video':
            #print(str(track.width)+"x"+str(track.height))
            return str(track.width)+":"+str(track.height)
    raise AssertionError("failed to read video info from " + input_file)

@app.task
def thumbnail(file_mp4, title):
    # Get random thumbnail from the original video
    # scale : 640x360
    print(HEADER + "Get thumbnail" + ENDC)
    command_line_fps = "ffmpeg -i "+file_mp4+" -vf  \"thumbnail,scale=640:360\" -frames:v 1 filesWorker/"+title+"/thumbnail.png"
    subprocess.call(command_line_fps,  stdout=FNULL, stderr=subprocess.STDOUT, shell=True)

@app.task
def encode_audio(time_ms, title):

    print(HEADER + "Audio encoding" + ENDC)

    if(os.path.exists("filesWorker/audio.m4a")):
        # ffmpeg -i input.m4a -c:a aac -strict -2 -force_key_frames expr:gte\(t,n_forced*4\) outaudio.m4a
        os.mkdir("filesWorker/"+title+"/audio")
        command_line = "ffmpeg -i filesWorker/audio.m4a -c:a aac -strict -2 -force_key_frames expr:gte\(t,n_forced*0.5\) filesWorker/outaudio.m4a"
        subprocess.call(command_line, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)
        print(WARNING + "\tEncoding" + ENDC)
        command_line = "ffmpeg -i filesWorker/outaudio.m4a -ss 0.5 -c:a copy filesWorker/outaudiog.m4a"
        #print(command_line)
        subprocess.call(command_line, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)
        command_line2 = "MP4Box -dash " + time_ms + " -profile live -segment-name 'out_dash$Number$' -out 'filesWorker/"+title+"/audio/mpd.mpd' filesWorker/outaudiog.m4a"
        subprocess.call(command_line2, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)
        print(WARNING + "\tDash segmentation" + ENDC)
    else:
        print(FAIL + "No audio to encode" + ENDC)

@app.task
def encode(bitrate, resolution):
    # ffmpeg -i origin.mov -c:v libx264 -b:v 1000k -x264opts keyint=12:min-keyint=1:scenecut=-1 out.h264
    if os.path.exists("watermarks/"+resolution+"/"+bitrate+".png"):
        command_line = "ffmpeg -y -i filesWorker/input.mp4 -i watermarks/"+resolution+"/"+bitrate+".png -filter_complex \"overlay=0:0\" -c:v libx264 -profile:v main -b:v " + bitrate + "k -x264opts keyint=12:min-keyint=12:scenecut=-1 -bf 0 -r 24 filesWorker/out" + bitrate + ".h264"
    else:
        command_line = "ffmpeg -y -i filesWorker/input.mp4 -c:v libx264 -profile:v main -b:v " + bitrate + "k -x264opts keyint=12:min-keyint=12:scenecut=-1 -bf 0 -r 24 filesWorker/out" + bitrate + ".h264"
    subprocess.call(command_line, stdout=FNULL, stderr=subprocess.STDOUT,  shell=True)
    print(OKGREEN + resolution + " - " + bitrate + "k encoded [OK]" + ENDC)

@app.task
def set_resolution(resolution):
    # ffmpeg -i origin.mov -c:v libx264 -b:v 1000k -x264opts keyint=12:min-keyint=1:scenecut=-1 out.h264

    if(get_video_size("filesWorker/video.mp4") == resolution):
        copyfile("filesWorker/video.mp4", "filesWorker/input.mp4")
        #os.rename("filesWorker/inputr.mp4", "filesWorker/input.mp4")
    else:
        command_line = "ffmpeg -y -i filesWorker/inputr.mp4 -profile:v main -preset veryslow -b:v 10000k -vf scale="+resolution+" filesWorker/input.mp4"
        subprocess.call(command_line, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)

@app.task
def mux(file_h264, quality):
    # ffmpeg - f h264 - i filenam.264 - vcodec copy newfile.mp4
    command_line = "ffmpeg -y -f h264 -i " + file_h264 + " -vcodec copy filesWorker/out" + quality + ".mp4"
    #print(command_line)
    subprocess.call(command_line, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)

@app.task
def remove_first_gop(file_h264, quality):
    # ffmpeg -i inputfile.h264 -ss 0.5 -vcodec copy outputfile.h264
    command_line = "ffmpeg -y -i " + file_h264 + " -ss 0.5 -vcodec copy filesWorker/out" + quality + "g.mp4"
    #print(command_line)
    subprocess.call(command_line, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)


@app.task
def dash_segmentation(file_mp4, time_ms, title):
    # MP4Box version > 5.1
    # MP4Box -dash 6000 -profile live -segment-name '$Bandwidth$/out$Bandwidth$_dash$Number$' -out mpd.mpd inputfile.mp4
    command_line = "MP4Box -dash " + time_ms + " -profile live -segment-name 'filesWorker/"+title+"/$Bandwidth$/out$Bandwidth$_dash$Number$' -out 'mpd.mpd' filesWorker/"+file_mp4
    #print(command_line)
    subprocess.call(command_line, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)
    print(OKGREEN + "\tDash segmentation [OK]" + ENDC)

@app.task
def dash_segmentation2(files_mp4, time_ms, title):
    # MP4Box version > 5.1
    # MP4Box -dash 6000 -profile live -segment-name '$Bandwidth$/out$Bandwidth$_dash$Number$' -out mpd.mpd inputfile.mp4
    output=""
    for mp4file in files_mp4:
        output += "filesWorker/"+mp4file+" "
    print("output = " + output)
    command_line = "MP4Box -dash " + time_ms + " -profile live -segment-name 'filesWorker/"+title+"/$Bandwidth$/out$Bandwidth$_dash$Number$' -out 'mpd.mpd' " + output
    print(command_line)
    subprocess.call(command_line, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)
    print(OKGREEN + "\tDash segmentation [OK]" + ENDC)

@app.task
def order_files(title):
    xmldoc = minidom.parse('mpd.mpd')
    rep = xmldoc.getElementsByTagName('Representation')
    for node in rep:
        # print(node.getAttribute('bandwidth'))
        shutil.move("mpd.mpd", "filesWorker/"+title+"/" + node.getAttribute('bandwidth') + "/mpd.mpd")

    # os.rename("filesWorker/" + node.getAttribute('bandwidth') + "/out" + node.getAttribute('bandwidth') + "_dash.mp4", "filesWorker/" + node.getAttribute('bandwidth') + "/init.mp4")
    # shutil.move("filesWorker/" + node.getAttribute('bandwidth') + "/init.mp4", "filesWorker/init.mp4")

@app.task
def delete_files():
    xmldoc = minidom.parse('filesWorker/mpd.mpd')
    rep = xmldoc.getElementsByTagName('Representation')
    for node in rep:
        #print(node.getAttribute('bandwidth'))
        shutil.move("filesWorker/mpd.mpd", "filesWorker/" + node.getAttribute('bandwidth') + "/mpd.mpd")

    os.rename("filesWorker/" + node.getAttribute('bandwidth') + "/out" + node.getAttribute('bandwidth') + "_dash.mp4", "filesWorker/" + node.getAttribute('bandwidth') + "/init.mp4")
    shutil.move("filesWorker/" + node.getAttribute('bandwidth') + "/init.mp4", "filesWorker/init.mp4")

@app.task
def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))

@app.task
def msEncoding(title,download_url,callback):
    # create folder
    directory = "filesWorker"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # get settings
    settings = get_settings("settings.ini")

    # get zip
    with open('filesWorker/'+title+'.zip', 'wb') as handle:
        response = requests.get(download_url, stream=True)

        if not response.ok:
            print("Something went wrong")

        for block in response.iter_content(1024):
            handle.write(block)

    # unzip
    zip_ref = zipfile.ZipFile("filesWorker/"+title+".zip", 'r')
    zip_ref.extractall("filesWorker")
    zip_ref.close()



    # Thumbnail
    # thumbnail("filesWorker/video.mp4", title)

    # Audio
    # encode_audio("6000", title)

    # # Video
    # print(HEADER + "Video encoding" + ENDC)
    #
    # for resolution in settings.sections():
    #
    #     set_resolution(resolution)
    #
    #     qualities = [e.strip() for e in settings.get(resolution, 'Bitrates').split(',')]
    #     allQualities = []
    #     for quality in qualities:
    #         encode(quality, resolution)
    #         remove_first_gop("filesWorker/out"+quality+".h264", quality)
    #         mux("filesWorker/out"+quality+".h264",quality)
    #         allQualities.append("'out"+quality+"g.mp4'")
    #         #dash_segmentation("'out"+quality+"g.mp4'", "6000", titled)
    #         #order_files(titled)
    #
    # dash_segmentation2(allQualities, "6000", title)
    # zipf = zipfile.ZipFile("filesWorker/"+title+".zip", 'w', zipfile.ZIP_DEFLATED, allowZip64=True)
    # zipdir("filesWorker/"+title, zipf)
    # zipf.close()
    print(HEADER + "Zipping files" + ENDC)

from celery import Celery
from pymediainfo import MediaInfo
import os
import shutil
from shutil import copyfile
import subprocess
import configparser
import zipfile
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
    response=""
    if(os.path.exists("filesWorker/"+title+"/audio.m4a")):
        # ffmpeg -i input.m4a -c:a aac -strict -2 -force_key_frames expr:gte\(t,n_forced*4\) outaudio.m4a

        # Create folders
        #if not os.path.exists("filesWorker/"+title+"/audio"):
            #os.makedirs("filesWorker/"+title+"/audio")

        command_line = "ffmpeg -i filesWorker/"+title+"/audio.m4a -c:a aac -strict -2 -force_key_frames expr:gte\(t,n_forced*0.5\) filesWorker/"+title+"/tmp/outaudio.m4a"
        subprocess.call(command_line, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)
        print(WARNING + "\tEncoding" + ENDC)
        command_line = "ffmpeg -i filesWorker/"+title+"/tmp/outaudio.m4a -ss 1 -c:a copy filesWorker/"+title+"/tmp/outaudiog.m4a"

        subprocess.call(command_line, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)
        #command_line2 = "MP4Box -dash " + time_ms + " -profile live -segment-name 'out_dash$Number$' -out 'filesWorker/"+title+"/audio/mpd.mpd' filesWorker/"+title+"/tmp/outaudiog.m4a"
        #subprocess.call(command_line2, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)
        print(WARNING + "\tDash segmentation" + ENDC)
        response = "filesWorker/"+title+"/tmp/outaudiog.m4a"
    else:
        print(FAIL + "No audio to encode" + ENDC)

    return response

@app.task
def encode(bitrate, resolution, title):
    # ffmpeg -i origin.mov -c:v libx264 -b:v 1000k -x264opts keyint=12:min-keyint=1:scenecut=-1 out.h264
    if os.path.exists("watermarks/"+resolution+"/"+bitrate+".png"):
        command_line = "ffmpeg -y -i filesWorker/"+title+"/tmp/input.mp4 -i watermarks/"+resolution+"/"+bitrate+".png -filter_complex \"overlay=0:0\" -c:v libx264 -profile:v main -b:v " + bitrate + "k -x264opts keyint=12:min-keyint=12:scenecut=-1 -bf 0 -r 24 filesWorker/"+title+"/tmp/out" + bitrate + ".h264"
    else:
        command_line = "ffmpeg -y -i filesWorker/"+title+"/tmp/input.mp4 -c:v libx264 -profile:v main -b:v " + bitrate + "k -x264opts keyint=12:min-keyint=12:scenecut=-1 -bf 0 -r 24 filesWorker/"+title+"/tmp/out" + bitrate + ".h264"
    subprocess.call(command_line, stdout=FNULL, stderr=subprocess.STDOUT,  shell=True)
    print(OKGREEN + resolution + " - " + bitrate + "k encoded [OK]" + ENDC)

@app.task
def set_resolution(resolution, title):
    # ffmpeg -i origin.mov -c:v libx264 -b:v 1000k -x264opts keyint=12:min-keyint=1:scenecut=-1 out.h264

    if(get_video_size("filesWorker/"+title+"/video.mp4") == resolution):
        copyfile("filesWorker/"+title+"/video.mp4", "filesWorker/"+title+"/tmp/input.mp4")
        #os.rename("filesWorker/inputr.mp4", "filesWorker/input.mp4")
    else:
        command_line = "ffmpeg -y -i filesWorker/"+title+"/video.mp4 -profile:v main -preset veryslow -b:v 10000k -vf scale="+resolution+" filesWorker/"+title+"/tmp/input.mp4"
        subprocess.call(command_line, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)

@app.task
def mux(file_h264, quality, title):
    # ffmpeg - f h264 - i filenam.264 - vcodec copy newfile.mp4
    command_line = "ffmpeg -y -f h264 -i " + file_h264 + " -vcodec copy filesWorker/"+title+"/tmp/out" + quality + ".mp4"
    #print(command_line)
    subprocess.call(command_line, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)

@app.task
def remove_first_gop(file_h264, quality, title):
    # ffmpeg -i inputfile.h264 -ss 0.5 -vcodec copy outputfile.h264
    command_line = "ffmpeg -y -f h264 -i " + file_h264 + " -ss 0.5 -vcodec copy filesWorker/"+title+"/tmp/out" + quality + "g.mp4"
    #print(command_line)
    subprocess.call(command_line, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)


@app.task
def dash_segmentation(file_mp4, time_ms, title):
    # MP4Box version > 5.1
    # MP4Box -dash 6000 -profile live -segment-name '$Bandwidth$/out$Bandwidth$_dash$Number$' -out mpd.mpd inputfile.mp4
    command_line = "MP4Box -dash " + time_ms + " -profile live -segment-name '$Bandwidth$/out$Bandwidth$_dash$Number$' -out 'mpd.mpd' filesWorker/"+file_mp4
    #print(command_line)
    subprocess.call(command_line, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)
    print(OKGREEN + "\tDash segmentation [OK]" + ENDC)

@app.task
def dash_segmentation2(files_mp4, time_ms, title):
    # MP4Box version > 5.1
    # MP4Box -dash 6000 -profile live -segment-name '$Bandwidth$/out$Bandwidth$_dash$Number$' -out mpd.mpd inputfile.mp4
    input=""
    for mp4file in files_mp4:
        input += mp4file+" "
    print("input = " + input)
    command_line = "MP4Box -dash " + time_ms + " -profile live -bs-switching no -segment-name '$Bandwidth$/out$Bandwidth$_dash$Number$' -out 'filesWorker/"+title+"/mpd.mpd' " + input
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
def zipusinglinux(path, dest):
    command_line = "zip -r " + dest + " " + path
    subprocess.call(command_line, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)

@app.task
def postContent(path, ytb_id, contentsupplying_url):
    r = requests.post(contentsupplying_url, files={ytb_id: open(path, 'rb')})
    return r

@app.task
def msEncoding(title,settings_url,download_url,callback):
    # create folder
    directory = "filesWorker"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # get settings
    with open('filesWorker/settings.ini', 'wb') as handle:
        response = requests.get(settings_url, stream=True)

        if not response.ok:
            print("Something went wrong")

        for block in response.iter_content(1024):
            handle.write(block)
    settings = get_settings("filesWorker/settings.ini")
    os.remove("filesWorker/settings.ini")

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

    # Init tmp
    if not os.path.exists("filesWorker/" + title + "/tmp"):
        os.makedirs("filesWorker/" + title + "/tmp")

    # Thumbnail
    thumbnail("filesWorker/"+title+"/video.mp4", title)

    # Audio
    audiofile = encode_audio("6000", title)

    # Video
    print(HEADER + "Video encoding" + ENDC)
    allQualities = []
    allQualities.append(audiofile)
    for resolution in settings.sections():
        set_resolution(resolution, title)

        qualities = [e.strip() for e in settings.get(resolution, 'Bitrates').split(',')]

        for quality in qualities:
            encode(quality, resolution, title)
            remove_first_gop("filesWorker/"+title+"/tmp/out"+quality+".h264", quality, title)
            #mux("filesWorker/"+title+"/tmp/out"+quality+".h264",quality, title)
            allQualities.append("filesWorker/"+title+"/tmp/"+"out"+quality+"g.mp4")
            #dash_segmentation("'out"+quality+"g.mp4'", "6000", titled)
            #order_files(titled)

    dash_segmentation2(allQualities, "6000", title)

    #zip result
    os.remove("filesWorker/"+title+".zip")
    shutil.rmtree("filesWorker/" + title + "/tmp")
    os.remove("filesWorker/" + title + "/video.mp4")
    os.remove("filesWorker/" + title + "/audio.m4a")

    os.chdir("filesWorker")
    #zipf = zipfile.ZipFile(title+".zip", 'w', zipfile.ZIP_DEFLATED, allowZip64=True)
    #zipdir(title, zipf)
    #zipf.close()
    zipusinglinux(title, title + '.zip');
    os.chdir("..")

    # callback
    postContent("filesWorker/"+title+".zip",title, callback)

    shutil.rmtree("filesWorker")

    print(HEADER + "Job over" + ENDC)

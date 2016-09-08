from celery import Celery
from pymediainfo import MediaInfo
import pafy
import os
import shutil
from shutil import copyfile
import subprocess
import ConfigParser
import zipfile
from xml.dom import minidom

# New celery worker connected to default RabbitMQ
app = Celery('tasks', backend='amqp', broker='amqp://')
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
    settings = ConfigParser.ConfigParser()
    settings.read(file_settings)
    return settings

@app.task
def clean():

    dir = 'files'
    try:
        os.stat(dir)
    except:
        os.mkdir(dir)
    shutil.rmtree(dir)
    os.makedirs(dir)
    print(OKGREEN + "Clean directory" + ENDC)

@app.task
def get_video_size(input_file):
    media_info = MediaInfo.parse(input_file)
    for track in media_info.tracks:
        if track.track_type == 'Video':
            #print(str(track.width)+"x"+str(track.height))
            return str(track.width)+":"+str(track.height)
    raise AssertionError("failed to read video info from " + input_file)

@app.task
def download_last_video(task):
    print(HEADER + "Download video" + ENDC)

    if(task == "latest"):
        # Subprocess get most recent video ID
        proc = subprocess.Popen(["python", "-c", "import ytsubs; ytsubs.do_it()"], stdout=subprocess.PIPE)

        # Get out of the subprocess which is the video id
        out = proc.communicate()[0]
    else:
        out = task
        #print out

    # New pafy object with video ID
    v = pafy.new(out)
    print(WARNING + "\tTitle : "+v.title + ENDC)
    print(WARNING + "\tDuration : "+v.duration + ENDC)

    # Get the best quality available
    s = v.getbestvideo(preftype="mp4", ftypestrict=False)
    sa = v.getbestaudio()

    # Download the video
    # print("Video file size is %s" % s.get_filesize())
    filename = s.download(filepath="files/inputr.mp4")  # starts download
    filename = sa.download(filepath="files/audio.m4a")  # starts download

    return v.title

@app.task
def thumbnail(file_mp4, title):
    # Get random thumbnail from the original video
    # scale : 640x360
    print(HEADER + "Get thumbnail" + ENDC)
    command_line_fps = "ffmpeg -i "+file_mp4+" -vf  \"thumbnail,scale=640:360\" -frames:v 1 files/"+title+"/thumbnail.png"
    subprocess.call(command_line_fps,  stdout=FNULL, stderr=subprocess.STDOUT, shell=True)

@app.task
def encode_audio(time_ms, title):

    print(HEADER + "Audio encoding" + ENDC)

    if(os.path.exists("files/audio.m4a")):
        # ffmpeg -i input.m4a -c:a aac -strict -2 -force_key_frames expr:gte\(t,n_forced*4\) outaudio.m4a
        os.mkdir("files/"+title+"/audio")
        command_line = "ffmpeg -i files/audio.m4a -c:a aac -strict -2 -force_key_frames expr:gte\(t,n_forced*0.5\) files/outaudio.m4a"
        subprocess.call(command_line, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)
        print(WARNING + "\tEncoding" + ENDC)
        command_line = "ffmpeg -i files/outaudio.m4a -ss 0.5 -c:a copy files/outaudiog.m4a"
        #print(command_line)
        subprocess.call(command_line, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)
        command_line2 = "MP4Box -dash " + time_ms + " -profile live -segment-name 'out_dash$Number$' -out 'files/"+title+"/audio/mpd.mpd' files/outaudiog.m4a"
        subprocess.call(command_line2, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)
        print(WARNING + "\tDash segmentation" + ENDC)
    else:
        print(FAIL + "No audio to encode" + ENDC)

@app.task
def encode(bitrate, resolution):
    # ffmpeg -i origin.mov -c:v libx264 -b:v 1000k -x264opts keyint=12:min-keyint=1:scenecut=-1 out.h264
    if os.path.exists("watermarks/"+resolution+"/"+bitrate+".png"):
        command_line = "ffmpeg -y -i files/input.mp4 -i watermarks/"+resolution+"/"+bitrate+".png -filter_complex \"overlay=0:0\" -c:v libx264 -profile:v main -b:v " + bitrate + "k -x264opts keyint=12:min-keyint=12:scenecut=-1 -bf 0 -r 24 files/out" + bitrate + ".h264"
    else:
        command_line = "ffmpeg -y -i files/input.mp4 -c:v libx264 -profile:v main -b:v " + bitrate + "k -x264opts keyint=12:min-keyint=12:scenecut=-1 -bf 0 -r 24 files/out" + bitrate + ".h264"
    subprocess.call(command_line, stdout=FNULL, stderr=subprocess.STDOUT,  shell=True)
    print(OKGREEN + resolution + " - " + bitrate + "k encoded [OK]" + ENDC)

@app.task
def set_resolution(resolution):
    # ffmpeg -i origin.mov -c:v libx264 -b:v 1000k -x264opts keyint=12:min-keyint=1:scenecut=-1 out.h264

    if(get_video_size("files/inputr.mp4") == resolution):
        copyfile("files/inputr.mp4", "files/input.mp4")
        #os.rename("files/inputr.mp4", "files/input.mp4")
    else:
        command_line = "ffmpeg -y -i files/inputr.mp4 -profile:v main -preset veryslow -b:v 10000k -vf scale="+resolution+" files/input.mp4"
        subprocess.call(command_line, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)

@app.task
def mux(file_h264, quality):
    # ffmpeg - f h264 - i filenam.264 - vcodec copy newfile.mp4
    command_line = "ffmpeg -y -f h264 -i " + file_h264 + " -vcodec copy files/out" + quality + ".mp4"
    #print(command_line)
    subprocess.call(command_line, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)

@app.task
def remove_first_gop(file_h264, quality):
    # ffmpeg -i inputfile.h264 -ss 0.5 -vcodec copy outputfile.h264
    command_line = "ffmpeg -y -i " + file_h264 + " -ss 0.5 -vcodec copy files/out" + quality + "g.mp4"
    #print(command_line)
    subprocess.call(command_line, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)


@app.task
def dash_segmentation(file_mp4, time_ms, title):
    # MP4Box version > 5.1
    # MP4Box -dash 6000 -profile live -segment-name '$Bandwidth$/out$Bandwidth$_dash$Number$' -out mpd.mpd inputfile.mp4
    command_line = "MP4Box -dash " + time_ms + " -profile live -segment-name 'files/"+title+"/$Bandwidth$/out$Bandwidth$_dash$Number$' -out 'mpd.mpd' files/"+file_mp4
    #print(command_line)
    subprocess.call(command_line, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)
    print(OKGREEN + "\tDash segmentation [OK]" + ENDC)


@app.task
def order_files(title):
    xmldoc = minidom.parse('mpd.mpd')
    rep = xmldoc.getElementsByTagName('Representation')
    for node in rep:
        #print(node.getAttribute('bandwidth'))
        shutil.move("mpd.mpd", "files/"+title+"/" + node.getAttribute('bandwidth') + "/mpd.mpd")

    #os.rename("files/" + node.getAttribute('bandwidth') + "/out" + node.getAttribute('bandwidth') + "_dash.mp4", "files/" + node.getAttribute('bandwidth') + "/init.mp4")
    #shutil.move("files/" + node.getAttribute('bandwidth') + "/init.mp4", "files/init.mp4")

@app.task
def delete_files():
    xmldoc = minidom.parse('files/mpd.mpd')
    rep = xmldoc.getElementsByTagName('Representation')
    for node in rep:
        #print(node.getAttribute('bandwidth'))
        shutil.move("files/mpd.mpd", "files/" + node.getAttribute('bandwidth') + "/mpd.mpd")

    os.rename("files/" + node.getAttribute('bandwidth') + "/out" + node.getAttribute('bandwidth') + "_dash.mp4", "files/" + node.getAttribute('bandwidth') + "/init.mp4")
    shutil.move("files/" + node.getAttribute('bandwidth') + "/init.mp4", "files/init.mp4")


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))

@app.task
def process(task, test):

    clean()

    settings = get_settings("settings.ini")
    if test == False:
        title = download_last_video(task)
    else:
        title = task[task.rindex("/")+1:task.rindex(".")]
        copyfile(task, "files/file.mp4")
        command_lineVid = "ffmpeg -y -i files/file.mp4 -vcodec copy -an files/inputr.mp4"
        command_lineAud = "ffmpeg -y -i files/file.mp4 -acodec copy -vn files/audio.m4a"
        subprocess.call(command_lineVid, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)
        subprocess.call(command_lineAud, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)
    titled = title.replace(" ", "_")
    titled = titled.replace("|", "")
    titled = titled.replace("/", "")

    os.mkdir("files/"+titled)
    # Thumbnail
    thumbnail("files/inputr.mp4", titled)

    # Audio
    encode_audio("6000", titled)

    #print settings.sections()
    print(HEADER + "Video encoding" + ENDC)

    for resolution in settings.sections():

        set_resolution(resolution)

        qualities = [e.strip() for e in settings.get(resolution, 'Bitrates').split(',')]

        for quality in qualities:
            encode(quality, resolution)
            remove_first_gop("files/out"+quality+".h264", quality)
            mux("files/out"+quality+".h264",quality)
            dash_segmentation("'out"+quality+"g.mp4'", "6000", titled)
            order_files(titled)

    zipf = zipfile.ZipFile("files/"+titled+".zip", 'w', zipfile.ZIP_DEFLATED)
    zipdir("files/"+titled, zipf)
    zipf.close()
    print(HEADER + "Zipping files" + ENDC)

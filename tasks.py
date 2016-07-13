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

@app.task
def get_settings(file_settings):
    settings = ConfigParser.ConfigParser()
    settings.read(file_settings)
    return settings

@app.task
def clean():
    dir = 'files'
    shutil.rmtree(dir)
    os.makedirs(dir)

@app.task
# def get_video_size(input_file):
def get_video_size(input_file):
    '''
    use mediainfo to compute the video size
    '''
    media_info = MediaInfo.parse(input_file)
    for track in media_info.tracks:
        if track.track_type == 'Video':
            print(str(track.width)+"x"+str(track.height))
            return str(track.width)+":"+str(track.height)
    raise AssertionError("failed to read video info from " + input_file)

@app.task
def download_last_video():
    # Subprocess get most recent video ID
    #proc = subprocess.Popen(["python", "-c", "import ytsubs; ytsubs.do_it()"], stdout=subprocess.PIPE)

    # Get out of the subprocess which is the video id
    #out = proc.communicate()[0]
    out = "pJt88dFv9Wg"
    print out

    # New pafy object with video ID
    v = pafy.new(out)
    print(v.title)
    print(v.duration)
    print(v.rating)
    print(v.author)
    print(v.length)
    print(v.keywords)
    print(v.thumb)
    print(v.videoid)
    print(v.viewcount)

    # Get the best quality available
    s = v.getbestvideo(preftype="mp4", ftypestrict=False)

    sa = v.getbestaudio()

    # Download the video
    print("Video file size is %s" % s.get_filesize())
    filename = s.download(filepath="files/inputr.mp4")  # starts download
    filename = sa.download(filepath="files/audio.m4a")  # starts download

@app.task
def convert_to_25_fps(file_mp4):

    # Convert to 25 fps
    command_line_fps = "ffmpeg -i files/input.mp4 -vcodec libx264 -vprofile high -preset slow -vb 6000k -maxrate 6000k -bufsize 1000k -r 25  files/input_25.mp4"
    command_line_fps_old = "ffmpeg -i files/input.mp4 -r 25 -y files/input_25.mp4"
    subprocess.call(command_line_fps, shell=True)

@app.task
def thumbnail(file_mp4):

    # Convert to 25 fps
    command_line_fps = "ffmpeg -i "+file_mp4+" -vf  \"thumbnail,scale=640:360\" -frames:v 1 files/thumbnail.png"
    subprocess.call(command_line_fps, shell=True)


@app.task
def unmux(file_mp4):
    ## Extract audio track (aac)
    # ffmpeg -i input.mp4 -vn -acodec copy out.aac
    #command_line_audio = "ffmpeg -i " + file_mp4 + " -vn -acodec copy files/out.aac"
    # subprocess.call(command_line_audio, shell=True)

    ## Extract video track (yuv)
    # ffmpeg -i video.mp4 -c:v rawvideo -pix_fmt yuv420p out.yuv
    # ffmpeg -i video.mts -vcodec copy -an -f h264 ffNT.h264
    command_line_video = "ffmpeg -i " + file_mp4 + " -c:v rawvideo -pix_fmt yuv420p files/out.yuv"
    subprocess.call(command_line_video, shell=True)

@app.task
def encode(bitrate):
    # ./h264enc welsenc1M.cfg
    command_line = "./tools/openH264/h264enc tools/openH264/welsenc/welsenc" + bitrate + ".cfg"
    subprocess.call(command_line, shell=True)

@app.task
def encode_audio(time_ms):
    # ffmpeg -i input.m4a -c:a aac -strict -2 -force_key_frames expr:gte\(t,n_forced*4\) outaudio.m4a
    os.mkdir("files/audio")
    command_line = "ffmpeg -i files/audio.m4a -c:a aac -strict -2 -force_key_frames expr:gte\(t,n_forced*0.5\) files/outaudio.m4a"
    subprocess.call(command_line, shell=True)
    command_line = "ffmpeg -i files/outaudio.m4a -ss 0.5 -c:a copy files/outaudiog.m4a"
    print(command_line)
    subprocess.call(command_line, shell=True)
    command_line2 = "cd files; ./../tools/MP4Box/MP4Box -dash " + time_ms + " -profile live -segment-name 'out_dash$Number$' -out 'audio/mpd.mpd' outaudiog.m4a"
    subprocess.call(command_line2, shell=True)


@app.task
def encode2(bitrate, resolution):
    # ffmpeg -i origin.mov -c:v libx264 -b:v 1000k -x264opts keyint=12:min-keyint=1:scenecut=-1 out.h264
    command_line = "ffmpeg -y -i files/input.mp4 -i tools/watermarks/"+resolution+"/"+bitrate+".png -filter_complex \"overlay=0:0\" -c:v libx264 -profile:v main -b:v " + bitrate + "k -x264opts keyint=12:min-keyint=12:scenecut=-1 -bf 0 -r 24 files/out" + bitrate + ".h264"
    subprocess.call(command_line, shell=True)

@app.task
def set_resolution(resolution):
    # ffmpeg -i origin.mov -c:v libx264 -b:v 1000k -x264opts keyint=12:min-keyint=1:scenecut=-1 out.h264

    if(get_video_size("files/inputr.mp4") == resolution):
        print("Resolution es already ok")
        copyfile("files/inputr.mp4", "files/input.mp4")
        #os.rename("files/inputr.mp4", "files/input.mp4")
    else:
        command_line = "ffmpeg -y -i files/inputr.mp4 -profile:v main -preset veryslow -b:v 10000k -vf scale="+resolution+" files/input.mp4"
        subprocess.call(command_line, shell=True)

@app.task
def mux(file_h264, quality):
    # ffmpeg - f h264 - i filenam.264 - vcodec copy newfile.mp4
    command_line = "ffmpeg -y -f h264 -i " + file_h264 + " -vcodec copy files/out" + quality + ".mp4"
    print(command_line)
    subprocess.call(command_line, shell=True)

@app.task
def remove_first_gop(file_h264, quality):
    # ffmpeg -i inputfile.h264 -ss 0.5 -vcodec copy outputfile.h264
    command_line = "ffmpeg -y -i " + file_h264 + " -ss 0.5 -vcodec copy files/out" + quality + "g.mp4"
    print(command_line)
    subprocess.call(command_line, shell=True)


@app.task
def dash_segmentation(file_mp4, time_ms):
    # MP4Box version > 5.1
    # MP4Box -dash 6000 -profile live -segment-name '$Bandwidth$/out$Bandwidth$_dash$Number$' -out mpd.mpd inputfile.mp4
    command_line = "cd files; ./../tools/MP4Box/MP4Box -dash " + time_ms + " -profile live -segment-name '$Bandwidth$/out$Bandwidth$_dash$Number$' -out 'mpd.mpd' "+ file_mp4
    print(command_line)
    subprocess.call(command_line, shell=True)


@app.task
def order_files():
    xmldoc = minidom.parse('files/mpd.mpd')
    rep = xmldoc.getElementsByTagName('Representation')
    for node in rep:
        print(node.getAttribute('bandwidth'))
        shutil.move("files/mpd.mpd", "files/" + node.getAttribute('bandwidth') + "/mpd.mpd")

    #os.rename("files/" + node.getAttribute('bandwidth') + "/out" + node.getAttribute('bandwidth') + "_dash.mp4", "files/" + node.getAttribute('bandwidth') + "/init.mp4")
    #shutil.move("files/" + node.getAttribute('bandwidth') + "/init.mp4", "files/init.mp4")

@app.task
def delete_files():
    xmldoc = minidom.parse('files/mpd.mpd')
    rep = xmldoc.getElementsByTagName('Representation')
    for node in rep:
        print(node.getAttribute('bandwidth'))
        shutil.move("files/mpd.mpd", "files/" + node.getAttribute('bandwidth') + "/mpd.mpd")

    os.rename("files/" + node.getAttribute('bandwidth') + "/out" + node.getAttribute('bandwidth') + "_dash.mp4", "files/" + node.getAttribute('bandwidth') + "/init.mp4")
    shutil.move("files/" + node.getAttribute('bandwidth') + "/init.mp4", "files/init.mp4")


@app.task
def process():

    clean()

    settings = get_settings("settings.ini")

    download_last_video()

    # Thumbnail
    thumbnail("files/inputr.mp4")

    # Audio
    encode_audio("6000")

    print settings.sections()

    for resolution in settings.sections():

        set_resolution(resolution)

        qualities = [e.strip() for e in settings.get(resolution, 'Bitrates').split(',')]

        for quality in qualities:
            encode2(quality, resolution)
            remove_first_gop("files/out"+quality+".h264", quality)
            mux("files/out"+quality+".h264",quality)
            dash_segmentation("'out"+quality+"g.mp4'", "6000")
            order_files()





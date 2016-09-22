import subprocess
import os
import pafy
import sys , getopt
import urllib2
import json
import jsonpickle
import requests
import zipfile
import shutil

FNULL = open(os.devnull, 'w')
HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'

baseurl = 'https://www.googleapis.com/youtube/v3'
my_key = 'AIzaSyAkomd5v3HWilMdrVgNwKyTs7o5RM5O7pw'
my_channel = 'UCjVRF7iMB-35SB6mVMSeHiA'

# check for missing inputs
if not my_key:
  print "YOUTUBE API KEY is wrong or missing."
  sys.exit(-1)

if not len(sys.argv) >= 0:
  print "Channel ID and (optionally) destination file must be specified as first and second arguments."
  sys.exit(-1)

def get_channel_for_user(user):
    url = baseurl + '/channels?part=id&id='+ my_channel + '&key=' + my_key
    response = urllib2.urlopen(url)
    data = json.load(response)
    return data['items'][0]['id']

def get_playlists(channel):
    playlists = []
    # we have to get the full snippet here, because there is no other way to get the channelId
    # of the channels you're subscribed to. 'id' returns a subscription id, which can only be
    # used to subsequently get the full snippet, so we may as well just get the whole lot up front.
    url = baseurl + '/subscriptions?part=snippet&channelId='+ channel + '&maxResults=10&key=' + my_key

    next_page = ''
    while True:
        # we are limited to 10 results. if the user subscribed to more than 10 channels
        # we have to make multiple requests here.
        response = urllib2.urlopen(url+next_page)
        data = json.load(response)
        subs = []
        for i in data['items']:
            if i['kind'] == 'youtube#subscription':
                subs.append(i['snippet']['resourceId']['channelId'])

        # actually getting the channel uploads requires knowing the upload playlist ID, which means
        # another request. luckily we can bulk these 50 at a time.
        purl = baseurl + '/channels?part=contentDetails&id='+ '%2C'.join(subs) + '&maxResults=50&key=' + my_key
        response = urllib2.urlopen(purl)
        data2 = json.load(response)
        for i in data2['items']:
            try:
                playlists.append(i['contentDetails']['relatedPlaylists']['uploads'])
            except KeyError:
                pass

        try: # loop until there are no more pages
            next_page = '&pageToken='+data['nextPageToken']
        except KeyError:
            break

    return playlists

def get_playlist_items(playlist):
    videos = []
    numberOfLast = '5'
    if playlist:
        # get the last 5 videos uploaded to the playlist
        url = baseurl + '/playlistItems?part=contentDetails&playlistId='+ playlist + '&maxResults='+numberOfLast+'&key=' + my_key
        response = urllib2.urlopen(url)
        data = json.load(response)
        for i in data['items']:
            if i['kind'] == 'youtube#playlistItem':
                videos.append(i['contentDetails']['videoId'])

    return videos

def getNewItems():

    # get all upload playlists of subbed channels
    playlists = get_playlists(get_channel_for_user(my_channel))

    # get the last 5 items from every playlist
    allitems = []
    for p in playlists:
        allitems.extend(get_playlist_items(p))

    return allitems


def postItems(allItems, contentsupplying_url):
    r = requests.post('http://'+contentsupplying_url+'/content', json=allItems)
    return r._content

def postContent(path, ytb_id, contentsupplying_url):
    r = requests.post('http://'+contentsupplying_url+'/content/' + ytb_id, files={ytb_id: open(path, 'rb')})
    return r

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))

def clean(dir):
    try:
        os.stat(dir)
    except:
        os.mkdir(dir)
    shutil.rmtree(dir)
    os.makedirs(dir)
    print(OKGREEN + "Clean directory" + ENDC)

####################################################################################################
#
#  Main function
#
####################################################################################################
def main(argv):
    # Get args
    contentsupplying_url = "localhost:8085"
    try:
        opts, args = getopt.getopt(argv, "hc:")
    except getopt.GetoptError:

        print WARNING + 'download.py -c <contentSupplying addr>' + ENDC
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print WARNING + 'download.py -c <contentSupplying addr>' + ENDC
            sys.exit()
        elif opt == "-c":
            contentsupplying_url = arg

    # clean folder
    clean("files")

    # init zip
    if not os.path.exists("files/zip"):
        os.makedirs("files/zip")

    print(HEADER + "Download video" + ENDC)

    # Get youtube last videos
    items = getNewItems()
    print "Items: " + jsonpickle.encode(items)
    newItemsString = postItems(items,contentsupplying_url)
    print "New Items: " + newItemsString
    newItems = jsonpickle.decode(newItemsString)

    for new in newItems:
        print "New video: " + new
        try:
            # New pafy object with video ID
            v = pafy.new(new)
            print(WARNING + "\tTitle : "+v.title + ENDC)
            print(WARNING + "\tDuration : "+v.duration + ENDC)


            # Get the best quality available
            s = v.getbestvideo(preftype="mp4", ftypestrict=False)
            sa = v.getbestaudio()
            outtext = {'title':v.title,'author':v.author,'description':v.description,'ytb_id':new}

            # Download the video
            print("Video file size is %s" % s.get_filesize())
            directory="files/"+new
            if not os.path.exists(directory):
                os.makedirs(directory)
            filename = s.download(filepath="files/"+new+"/video.mp4")  # starts download
            filename = sa.download(filepath="files/"+new+"/audio.m4a")  # starts download
            textfile = open("files/"+new+"/infos.json", "w")
            textfile.write(jsonpickle.encode(outtext))
            textfile.close()

            #Zip
            os.chdir("files")
            zipf = zipfile.ZipFile("zip/" + new + ".zip", 'w', zipfile.ZIP_DEFLATED, allowZip64=True)
            zipdir(new, zipf)
            zipf.close()
            os.chdir("..")
            postContent("files/zip/" + new + ".zip", new, contentsupplying_url)
        except :
            print "One stange error with youtube"


    #return v.title

if __name__ == "__main__":
   main(sys.argv[1:])

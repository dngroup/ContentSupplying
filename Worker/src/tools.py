import subprocess
from xml.dom import minidom
import os
import shutil
import requests

FNULL = open(os.devnull, 'w')
HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'

def delete_files():
    xmldoc = minidom.parse('filesWorker/mpd.mpd')
    rep = xmldoc.getElementsByTagName('Representation')
    for node in rep:
        #print(node.getAttribute('bandwidth'))
        shutil.move("filesWorker/mpd.mpd", "filesWorker/" + node.getAttribute('bandwidth') + "/mpd.mpd")

    os.rename("filesWorker/" + node.getAttribute('bandwidth') + "/out" + node.getAttribute('bandwidth') + "_dash.mp4", "filesWorker/" + node.getAttribute('bandwidth') + "/init.mp4")
    shutil.move("filesWorker/" + node.getAttribute('bandwidth') + "/init.mp4", "filesWorker/init.mp4")


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))


def zipusinglinux(path, dest):
    command_line = "zip -r " + dest + " " + path
    subprocess.call(command_line, stdout=FNULL, stderr=subprocess.STDOUT, shell=True)


def postContent(path, ytb_id, contentsupplying_url):
    headers = {
        'content-type': 'application/zip',
        'Content-Disposition': 'attachment; filename="'+ytb_id+'"',
    }
    with open(path,'br') as f:
        r = requests.post(contentsupplying_url,data=f,headers=headers)
    return r
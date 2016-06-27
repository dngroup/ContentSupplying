import subprocess
import pafy

# Subprocess get most recent video ID
proc = subprocess.Popen(["python", "-c", "import ytsubs; ytsubs.do_it()"], stdout=subprocess.PIPE)

# Get out of the subprocess which is the video id
out = proc.communicate()[0]
print out

# New pafy object with video ID
v = pafy.new(out)

# Get the best quality available
s = v.getbest()

# Download the video
print("Video file size is %s" % s.get_filesize())
filename = s.download()  # starts download

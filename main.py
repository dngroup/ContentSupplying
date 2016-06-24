import subprocess
import pafy

proc = subprocess.Popen(["python", "-c", "import ytsubs; ytsubs.do_it()"], stdout=subprocess.PIPE)
out = proc.communicate()[0]
print out
v = pafy.new(out)
s = v.getbest()
print("Size is %s" % s.get_filesize())
filename = s.download()  # starts download

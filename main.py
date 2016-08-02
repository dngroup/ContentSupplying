from tasks import process
import os
import sys, getopt

FNULL = open(os.devnull, 'w')
WARNING = '\033[93m'
ENDC = '\033[0m'


def main(argv):

   try:
      opts, args = getopt.getopt(argv,"hlif:",["ifile="])
   except getopt.GetoptError:
      print WARNING + 'for particular youtube video: main.py -i <video_id>' + ENDC
      print WARNING + 'for latest among subscribed: main.py -l' + ENDC
      print WARNING + 'for a local video: main.py -f <file path>' + ENDC
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print WARNING + 'for particular youtube video : main.py -i <video_id>' + ENDC
         print WARNING + 'for latest among subscribed : main.py -l' + ENDC
         print WARNING + 'for a local video: main.py -f <file path>' + ENDC
         sys.exit()
      elif opt in ("-i", "--ifile"):
         print 'Video is "', arg
         process(arg, False)
      elif opt in  ("-l"):
         print "latest"
         process("latest", False)
      elif opt in  ("-f"):
         print 'Video is "', arg
         print 'Title is "', arg[arg.rindex("/")+1:arg.rindex(".")]
         process(arg, True)

if __name__ == "__main__":
   main(sys.argv[1:])


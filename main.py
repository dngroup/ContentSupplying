from tasks import process
import os
import sys, getopt

FNULL = open(os.devnull, 'w')
WARNING = '\033[93m'
ENDC = '\033[0m'


def main(argv):

   try:
      opts, args = getopt.getopt(argv,"hli:",["ifile="])
   except getopt.GetoptError:
      print WARNING + 'for particular youtube video : test.py -i <video_id>' + ENDC
      print WARNING + 'for latest among subscribed : test.py -l' + ENDC
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print WARNING + 'for particular youtube video : test.py -i <video_id>' + ENDC
         print WARNING + 'for latest among subscribed : test.py -l' + ENDC
         sys.exit()
      elif opt in ("-i", "--ifile"):
         print 'Video is "', arg
         process(arg)
      elif opt in  ("-l"):
          print "latest"
          process("latest")

if __name__ == "__main__":
   main(sys.argv[1:])


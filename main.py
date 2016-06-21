import pafy

v = pafy.new("R76jxg-bC18")
s = v.getbest()
print("Size is %s" % s.get_filesize())
filename = s.download()  # starts download
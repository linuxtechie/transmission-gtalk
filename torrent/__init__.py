import imp
import os, string
from math import log
from config import BOT_BASE_DIR

transmissionClass = imp.load_source('test', os.path.join(os.path.join(BOT_BASE_DIR, 'transmission-remote-cli'), 'transmission-remote-cli'))


def sizeof_fmt(size,precision=2):
  suffixes=['B','KB','MB','GB','TB','PB']
  suffixIndex = 0
  while size > 1024:
      suffixIndex += 1 #increment the index of the suffix
      size = size/1024.0 #apply the division
  return "%.*f %s"%(precision,size,suffixes[suffixIndex])

def trunc(s,min_pos=0,max_pos=70,suffix='.'):
    s = s.strip()
    l = len(s)
    if l >= max_pos:
      return s[0:max_pos-3] + suffix * 3
    return s + suffix * (max_pos - l)

class TorrentData:
  def __init__(self):
    self.tid       = ""
    self.tname     = ""
    self.tstatus   = -1
    self.tsize     = -1
    self.tseeders  = -1
    self.tleechers = -1
    self.tdownloaded = -1
  def setItem(self, item):
    self.tid       = str(item['id'])
    t = item['name']
    t = filter(lambda x: x in string.printable, t)
    t = trunc(t)
    
#    try:
#      t = trunc(item['name'].encode('utf-8', errors='ignore'))
#    except:
#      t = trunc(item['name'].encode('utf-8'))
#
    self.tname     = t
    self.tsize     = item['sizeWhenDone']
    self.tstatus   = item['status']
    self.tseeders  = item['seeders']
    self.tleechers = item['leechers']
    self.tdownloaded = item['haveValid'] + item['haveUnchecked']

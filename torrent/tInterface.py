import imp
from config import BOT_BASE_DIR, TORRENT_PASSWORD, TORRENT_USER,\
  TRANSMISSION_SERVER, TRANSMISSION_SERVER_PORT, TRANSMISSION_SERVER_RPC, TRANSMISSION_LOG_FILE
import os
import logging, datetime, time
from zlogger import ZRotatingFileHandler
from torrent import TorrentData, sizeof_fmt

transmissionClass = imp.load_source('test', os.path.join(os.path.join(BOT_BASE_DIR, 'transmission-remote-cli'), 'transmission-remote-cli'))

NEWTORRENT            = 1
UPDATEDTORRENT        = 2
REMOVEDTORRENT        = 3
COMPLETEDTORRENT      = 4
DOWNLOADINGTORRENT    = 5
UNKNOWNSTATE          = 6
TORRENT_PAUSED        = "PAUSED"
TORRENT_PAUSE_TIME    = "TORRENT_PAUSE_TIME"

tlogger = logging.getLogger('transmission')
tlogger.setLevel(logging.DEBUG)
hdlr = ZRotatingFileHandler(TRANSMISSION_LOG_FILE, maxBytes=5*1024*1024, backupCount=100,
    compress_mode="zip")  
hdlr.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
tlogger.addHandler(hdlr)


class TorrentInterface:
  def __init__(self, db, func):
    self.transmissionShelf             = db
    self.buckets        = {}
    self.torrentList    = None
    self.func           = func
      
  def appendToBucket(self, bucket, tdata):
    if bucket not in self.buckets.keys():
      self.buckets[bucket] = []
    self.buckets[bucket].append(tdata)
    
  def getbucketList(self, bucket):
    if bucket in self.buckets.keys():
      return self.buckets[bucket]
    return []

  def getTransmission(self):
    try:
      return transmissionClass.Transmission(TRANSMISSION_SERVER, TRANSMISSION_SERVER_PORT, TRANSMISSION_SERVER_RPC, TORRENT_USER, TORRENT_PASSWORD)
    except:
      tlogger.error("Unable to connect to transmission")
      return None

  def process(self):
    
    transmission = self.transmission = self.getTransmission()
    if transmission == None:
      return
    tlogger.debug("Checking torrent updates")
    transmissionShelf = self.transmissionShelf
    currentList = []
    self.torrentList = transmission.get_torrent_list([{'name': 'name', 'reverse': False}])
    for item in self.torrentList:
      tdata = TorrentData()
      tdata.setItem(item)
      currentList.append(tdata.tid)

      if not transmissionShelf.has_key(tdata.tid):
        tlogger.debug("New torrent " + tdata.tname)
        transmissionShelf[tdata.tid] = tdata
        self.appendToBucket(NEWTORRENT, tdata)
        continue

      if transmissionShelf[tdata.tid].tstatus != tdata.tstatus:
        tlogger.debug("Updated torrent " + tdata.tname)
        self.appendToBucket(UPDATEDTORRENT, tdata)
        transmissionShelf[tdata.tid] = tdata

      transmissionShelf[tdata.tid] = tdata

      if tdata.tdownloaded > 0 and (tdata.tdownloaded == tdata.tsize):
        self.appendToBucket(COMPLETEDTORRENT, tdata)
        tlogger.debug("Completed torrent " + tdata.tname + ", it will be removed from transmission server")
        transmission.remove_torrent(int(tdata.tid))
        continue
      
      if tdata.tstatus == transmissionClass.Transmission.STATUS_DOWNLOAD:
#        tlogger.debug("Downloading torrent " + tdata.tname)
        self.appendToBucket(DOWNLOADINGTORRENT, tdata)
        continue
      
      self.appendToBucket(UNKNOWNSTATE, tdata)

    for itm in transmissionShelf.keys():
      if itm not in currentList :
        if transmissionShelf[itm] != "TorrentData": continue
        self.appendToBucket(REMOVEDTORRENT, transmissionShelf[itm])
        self.func("Removing torrent " + transmissionShelf[itm].tname + ", I had its records but it's no longer with transmission server")
        transmissionShelf.pop(itm)
        
    if DOWNLOADINGTORRENT not in self.buckets.keys() and NEWTORRENT not in self.buckets.keys():
      startTorrent = False

      if transmissionShelf.has_key(TORRENT_PAUSED) and transmissionShelf.has_key(TORRENT_PAUSE_TIME):
        tlogger.debug("Torrent paused at : " + transmissionShelf.get(TORRENT_PAUSED).isoformat(' '))
        tlogger.debug("Current time : " + datetime.datetime.now().isoformat(' '))
        tDelta = datetime.datetime.now() - transmissionShelf.get(TORRENT_PAUSED)
        tlogger.debug("Delta: " + str(tDelta))
    
        hours_timeout = transmissionShelf.get(TORRENT_PAUSE_TIME)
        if tDelta > datetime.timedelta(hours=hours_timeout):
          startTorrent = True
      else:
        startTorrent = True
           
      if startTorrent:
        if UNKNOWNSTATE in self.buckets.keys():
          tdata = self.buckets[UNKNOWNSTATE][0]
          transmission.start_torrent(int(tdata.tid))
          self.func("Starting torrent \"%s\" Size: %s/%s" % (tdata.tname, sizeof_fmt(tdata.tdownloaded), sizeof_fmt(tdata.tsize)))
    
        
  def sendMessages(self):
    transmission = self.transmission
    if not transmission: return
    if len(self.getbucketList(UPDATEDTORRENT)) > 0:
      message = ""
      for itm in self.getbucketList(UPDATEDTORRENT):
        for t in self.torrentList:
          if str(t['id']) != itm.tid:
            continue
          message = message + "\n" + "Updated torrent \"%s\" Size: %s, Status: %s" % (itm.tname, sizeof_fmt(itm.tdownloaded), transmission.get_status(t))
      self.func(message)

    if len(self.getbucketList(NEWTORRENT)) > 0:
      message = ""  
      for itm in self.getbucketList(NEWTORRENT):
        message = message + "\n" + "Added new torrent \"%s\" Size: %s" % (itm.tname, sizeof_fmt(itm.tsize))
      self.func(message)

    if len(self.getbucketList(COMPLETEDTORRENT)) > 0:
      message = ""  
      for itm in self.getbucketList(COMPLETEDTORRENT):
        message = message + "\n" + "Completed torrent \"%s\" Size: %s, removing from transmission server." % (itm.tname, sizeof_fmt(itm.tsize))
      self.func(message)

#    if len(self.getbucketList(DOWNLOADINGTORRENT)) > 0:    
#      message = ""  
#      for itm in self.getbucketList(DOWNLOADINGTORRENT):
#        message = message + "\n" + "Torrent downloading \"%s\" Size: %s" % (itm.tname, sizeof_fmt(itm.tdownloaded))
#      self.func(message)

#    if len(self.getbucketList(UNKNOWNSTATE)) > 0:
#      message = ""  
#      for itm in self.getbucketList(UNKNOWNSTATE):
#        message = message + "\n" + "Torrent paused \"%-50s\" Size: %s" % (itm.tname, sizeof_fmt(itm.tsize))
#      tlogger.info(message)

    if len(self.getbucketList(REMOVEDTORRENT)) > 0:
      message = ""  
      for itm in self.getbucketList(REMOVEDTORRENT):
        message = message + "\n" + "Torrent was removed \"%-50s\" Size: %s from transmission server" % (itm.tname, sizeof_fmt(itm.tdownloaded))
      self.func(message)


  def stop_torrents(self, timeout):
      transmission = self.getTransmission()
      if not transmission: return
      transmissionShelf = self.transmissionShelf
#      if not transmissionShelf.get(TORRENT_PAUSED):
      transmissionShelf[TORRENT_PAUSED] = datetime.datetime.now()
      transmissionShelf[TORRENT_PAUSE_TIME] = timeout
      
      for item in transmission.get_torrent_list([{'name': 'name', 'reverse': False}]):
        transmission.stop_torrent(int(item['id']))
      tlogger.debug("Stopped all the torrents at: " + datetime.datetime.now().isoformat(' '))
        
  def startTorrent(self, i):
      transmission = self.getTransmission()
      if not transmission: return False
      
      transmissionShelf = self.transmissionShelf
      if transmissionShelf.has_key(TORRENT_PAUSED):
        transmissionShelf.pop(TORRENT_PAUSED)
      
      transmission.start_torrent(i)
      tlogger.debug("Disabling stopping of all the torrents at: " + datetime.datetime.now().isoformat(' '))
      return True
    

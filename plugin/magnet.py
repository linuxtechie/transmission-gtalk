from errbot.botplugin import BotPlugin
from errbot import botcmd
from subprocess import Popen
import tempfile
from torrent import transmissionClass, sizeof_fmt
from config import TORRENT_USER, TORRENT_PASSWORD, TRANSMISSION_SERVER, TRANSMISSION_SERVER_PORT, TRANSMISSION_SERVER_RPC,\
  GTALK_ANNOUNCEMENT_LIST, BOT_DATA_DIR, HIPCHAT_MODE, CHATROOM_PRESENCE,\
  CHATROOM_FN
import logging
from torrent import TorrentData
import xmpp
import os
from torrent.tInterface import TorrentInterface
from threading import Timer
import shelve


MAGNET_DB = BOT_DATA_DIR + os.sep + 'transmission.db'

class Magnet(BotPlugin):
    connected = False
    actived = False

    def sendMessage(self, message):
      for rcvr in GTALK_ANNOUNCEMENT_LIST:
        try:
          message = xmpp.Message(rcvr, message)
          message.setAttr('type', 'chat')
          self.bare_send(message)
        except Exception:
          logging.exception("Exception occurred!")
          
    
    
    def do_announcement(self):
        if not self.actived:
          return
        obj = TorrentInterface(self.transmissionShelf, self.sendMessage)
        obj.process()
        obj.sendMessages()
        

    def callback_connect(self):
        logging.info('Callback_connect')
        if not self.connected:
            self.connected = True
  
    def do_command(self, cmd):
      outputlog = tempfile.TemporaryFile()
      p = Popen(cmd , shell=True, stdin=None, stdout=outputlog, stderr=outputlog)
      p.wait()
      outputlog.seek(0)
      text = outputlog.read()
      outputlog.close()
      return "%s\nCompleted task with : %d" %(text, p.returncode)

    def get_transmission_session(self):
      try:
        transmission = transmissionClass.Transmission(TRANSMISSION_SERVER,TRANSMISSION_SERVER_PORT,TRANSMISSION_SERVER_RPC,TORRENT_USER,TORRENT_PASSWORD)
      except Exception:
        logging.exception("Exception while accessing Transmission server, not doing anything.")
        return None
      return transmission

    @botcmd(template='list')
    def list_torrents(self, mess, args):
        return self.list_torrent(mess, args)

    @botcmd(template='list')
    def list_torrent(self, mess, args):
      """ Displays list of all queued up torrents.
      """
      t = self.get_transmission_session()
      if not t:
        return {}
      list_t = []
      for item in t.get_torrent_list([{'name': 'name', 'reverse': False}]):
          tdata = TorrentData()
          tdata.setItem(item)
          tdata.tsize = sizeof_fmt(tdata.tsize)
          tdata.tdownloaded = sizeof_fmt(tdata.tdownloaded)
          tdata.tstatus = t.get_status(item)
          list_t.append(tdata)
      return {'data':list_t}

    @botcmd
    def start_torrent(self, mess, args):
      """ Start torrent.
      """
      if len(args) < 1:
        return "Please mention the torrent"
      obj = TorrentInterface(self.transmissionShelf, self.sendMessage)
      if obj.startTorrent(int(args)):
        return "Started torrent %s" % args
      else:
        return "Couldn't connect with torrent server, failed"

    @botcmd
    def stop_torrent(self, mess, args):
      """ Stop torrent.
      """
      if len(args) < 1:
        return "Please mention the torrent"
      t = self.get_transmission_session()
      if t:
        t.stop_torrent(int(args))
        return "Stopped torrent %s" % args
      return "Couldn't connect with torrent server, failed"

    @botcmd
    def add_torrent(self, mess, args):
      """ Add torrent as specified
      """
      if len(args) < 1:
        return "Please mention the URL"
      t = self.get_transmission_session()
      if t:
        m = t.add_torrent(args)
        self.stop_torrents(mess, "1")
        return "Tried adding torrent %s %s" % (args,m)
      return "Couldn't connect with torrent server, failed"
    
    @botcmd
    def stop_torrents(self, mess, args):
      """ Stop all torrents for the specified timeout.
      """
      obj = TorrentInterface(self.transmissionShelf, self.sendMessage)
      if len(args) < 1:
         timeout = 1
      else:
         timeout = int(args)
      obj.stop_torrents(timeout)
      return "Stopped all torrents for " + str(timeout) + " hours"

    @botcmd
    def disk_status(self, mess, args):
      """ Disk status
      """
      return self.do_command("df -h")
      

    @botcmd
    def process_status(self, mess, args):
      """ Process status
      """
      return self.do_command("ps -ef")


    def activate(self):
      self.actived=True
      logging.info("Opening torrent database.")
      self.transmissionShelf = shelve.DbfilenameShelf(MAGNET_DB, protocol= -1)
      self.start_poller(10 , self.do_announcement) 
      super(Magnet, self).activate()

    def deactivate(self):
      logging.info("Closing torrent database.")
      self.actived=False
      self.transmissionShelf.close()
      super(Magnet, self).deactivate()

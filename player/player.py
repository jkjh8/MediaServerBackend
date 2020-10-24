# -*- coding: utf-8 -*-
import sys, vlc, socket, os.path, threading, json, re
from ast import literal_eval
from _thread import *
from time import sleep
from player_api import api
from time_format import timeFormat
from pymongo import MongoClient

db_client = MongoClient("mongodb://localhost:27017/MediaServer")
db = db_client['MediaServer']

instance = vlc.Instance()
player = instance.media_player_new()

port = 12302
MEDIA_PATH = os.path.abspath('./media/')

class PlayerServer():    
    def __init__(self):
        self.playlist = None
        self.udpSendSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('127.0.0.1', port))
        print("Udp Server Start {} : {}".format('127.0.0.1', 12302))
        self.setup = db.setup.find_one({})
        self.mp = media_Player(self.setup)
        if self.setup['poweronplay'] == True:
            self.play_id = 0
            self.playid()

    def run(self):
        while True:
            data, info = self.sock.recvfrom(65535)
            recv_Msg = data.decode()
            # try:
            if recv_Msg.startswith('stop'):
                self.mp.stop()
            elif recv_Msg.startswith('pause'):
                self.mp.pause()
            elif recv_Msg.startswith('playid'):
                self.play_id = int(re.findall('\d+', recv_Msg)[0])
                self.playid()
            elif recv_Msg.startswith('play'):
                func, file = recv_Msg.split(",")
                self.play(file)
            elif recv_Msg.startswith('refresh'):
                self.setup = db.setup.find_one({})
            else:
                rtmsg = api(recv_Msg, db)
                self.setup = db.setup.find_one({})                
                start_new_thread(self.udpSender, ('file_error',))
            # except:
            #     self.udpSender("unknown message")

    def play(self, playfile):
        file = os.path.join(MEDIA_PATH, playfile)
        if os.path.isfile(file):
            self.mp.play(file)
            start_new_thread(self.udpSender, ('play,{}'.format(playfile),))
        else:
            start_new_thread(self.udpSender, ('file_error',))

    def playid(self):
        if self.play_id < int(db.playlist.count({})):
            file = db.playlist.find_one({'playid': self.play_id}, { 'complete_name': 1 })['complete_name']
            if os.path.isfile(file):
                start_new_thread(self.udpSender, ('self.play_id,{}'.format(self.play_id),))
                self.play(file)
            else:
                start_new_thread(self.udpSender, ('file_error',))
        else:
            start_new_thread(self.udpSender, ('out_of_playlist_range',))

    def udpSender(self, msg):
        print(msg)
        print(self.setup['rtIp'], self.setup['rtPort'])
        self.udpSendSock.sendto(msg.encode(), (self.setup['rtIp'], self.setup['rtPort']))
    
    def songFinished(self, play_file):
        if self.setup['loop_one'] == True:
            self.playid()
            return
        elif self.setup['loop'] == True:
            if self.play_id <= db.playlist.count({}):
                self.play_id = 0
            else:
                self.play_id = self.play_id + 1
            print(self.play_id)
            self.playid()
            return
        elif self.setup['endclose'] == True:
            self.mp.stop()           

class media_Player():
    def __init__(self, setup):
        self.setup = setup
        # self.windowthread = threading.Thread(target=self.create_window)
        # self.windowthread.start()
        self.mediafile = None
        self.curr_time = None
        self.duration = None
        self.setNewPlayer()
        self.fullscreen()

    def setNewPlayer(self):
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        # self.player.set_hwnd(self.window.winfo_id())
        self.setEventManager()

    def create_window(self):
        self.window = tkinter.Tk()
        # self.window.overrideredirect(True)
        self.window.protocol('WM_DELETE_WINDOW', self.closed_window)
        self.window.configure(bg="black")
        self.window.geometry("800x480")
        self.window.title('MEDIA PLAYER')
        self.window.iconbitmap(default = 'favicon_player.ico') 
        self.window.mainloop()

    def closed_window(self):
        print('window closed')        

    def setEventManager(self):
        self.Event_Manager = self.player.event_manager()
        self.Event_Manager.event_attach(vlc.EventType.MediaPlayerEndReached, self.songFinished) #meida end
        self.Event_Manager.event_attach(vlc.EventType.MediaPlayerLengthChanged, self.getMediaLength, self.player) #media length
        self.Event_Manager.event_attach(vlc.EventType.MediaPlayerTimeChanged, self.getCurrentTime, self.player) #emdia get currnet time
    
    def setMedia(self, mediaFile):
        self.media = self.instance.media_new(mediaFile)
        self.player.set_media(self.media)

    def play(self, mediaFile):
        print(mediaFile)
        if self.mediafile == mediaFile: self.player.stop()
        else: self.mediafile = mediaFile; self.setMedia(mediaFile)
        if not self.player.get_fullscreen():
            self.fullscreen()
        self.player.play()

    def pause(self):
        self.player.pause()

    def stop(self):
        self.mediafile = None
        self.player.stop()

    def fullscreen(self):
        try:
            self.player.set_fullscreen(self.setup['fullscreen'])
        except:
            self.player.set_fullscreen(True)
        # try:
        #     self.window.attributes("-fullscreen", self.setup['fullscreen'])
            
        # except:
        #     self.window.attributes("-fullscreen", True)

    def songFinished(self,evnet):
        start_new_thread(app.songFinished, (self.mediafile,))
        self.curr_time = None
        self.duration = None
        
        start_new_thread(app.udpSender, ('end',))

    def getMediaLength(self, time, player):
        sendTime = timeFormat(time.u.new_length)
        if self.duration != sendTime:
            self.duration = sendTime
            start_new_thread(app.udpSender, ('length,{}'.format(sendTime),))

    def getCurrentTime(self, time, player):
        if app.setup['progress']:
            start_new_thread(self.currentTimeProcess, (time,))
    
    def currentTimeProcess(self, time):
        sendTime = timeFormat(time.u.new_time)
        if self.curr_time != sendTime:
            self.curr_time = sendTime
            app.udpSender('current,{}'.format(sendTime))
        

if __name__ == "__main__":
    app = main_UdpServer()
    app.run()

# -*- coding: utf-8 -*-
import sys, vlc, socket, os.path, threading
from _thread import *
from time import sleep

instance = vlc.Instance()
player = instance.media_player_new()

class main_UdpServer():
    def __init__(self):
        port = 12302
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((socket.gethostbyname(socket.gethostname()), port))
        print("Udp Server Start {} : {}".format(socket.gethostbyname(socket.gethostname()), port))

    def run(self):
        while True:
            data, info = self.sock.recvfrom(65535)
            recv_Msg = data.decode()
            print(recv_Msg)
            self.dataParcing(recv_Msg)
            
    def dataParcing(self, data):
        if data == "play":
            mp.play("1.mp4")
        elif data == "stop":
            mp.stop()

class media_Player():
    def __init__(self):
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

    def setNewPlayer(self):
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

    def setEventManager(self):
        self.Event_Manager = self.player.event_manager()
        self.Event_Manager.event_attach(vlc.EventType.MediaPlayerEndReached, self.songFinished) #meida end
        self.Event_Manager.event_attach(vlc.EventType.MediaPlayerLengthChanged, self.getMediaLength, self.player) #media length
        self.Event_Manager.event_attach(vlc.EventType.MediaPlayerTimeChanged, self.getCurrentTime, self.player) #emdia get currnet time
    
    def setMedia(self, mediaFile):
        self.media = self.instance.media_new(mediaFile)
        self.player.set_media(self.media)

    def play(self, mediaFile):
        print("Play Media = {}".format(mediaFile))
        print(self.player.get_state().value)
        if not self.player.is_playing():
            if not self.player:
                self.setNewPlayer()
                print("media player refresh")
            self.setEventManager()
            self.setMedia(mediaFile)
            self.player.play()
        self.player.set_time(0)
        
        

    def stop(self):
        self.player.stop()
        
    def songFinished(self,evnet):
        print("song Finish")

    def getMediaLength(self, time, player):
        sendTime = self.timeFormat(time.u.new_length)
        print(sendTime)

    def getCurrentTime(self, time, player):
        sendTime = self.timeFormat(time.u.new_time)
        print(sendTime)

    def timeFormat(self, ms):
        time = ms/1000
        min, sec = divmod(time, 60)
        hour, min = divmod(min, 60)
        return ("%02d:%02d:%02d" % (hour, min, sec))


if __name__ == "__main__":
    mp = media_Player()
    app = main_UdpServer()
    app.run()
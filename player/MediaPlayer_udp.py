# -*- coding: utf-8 -*-
import sys, vlc, socket, os.path, threading, json
from _thread import *
from time import sleep

instance = vlc.Instance()
player = instance.media_player_new()

rtIp = '127.0.0.1'
rtPort = 9999


class main_UdpServer():
    global rtIp, rtPort
    def __init__(self):
        port = 12302
        self.playlist = None
        self.udpSendSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('127.0.0.1', port))
        print("Udp Server Start {} : {}".format('127.0.0.1', port))

    def playlist_Refresh(self):
        with open('playlist.json') as playlist_file:
            self.playlist = json.load(playlist_file)

    def run(self):
        while True:
            data, info = self.sock.recvfrom(65535)
            recv_Msg = data.decode()
            print(recv_Msg)
            self.dataParcing(recv_Msg)
            
    def dataParcing(self, data):
        if data == "stop":
            mp.stop()
        else:
            comm = data.split(',')
            if comm[0] == 'play':
                file_path = os.path.abspath('./media/')
                file = os.path.join(file_path, comm[1])
                print(file)
                if os.path.isfile(file):
                    mp.play(file)
                    start_new_thread(self.udpSender, ('play,{}'.format(comm[1]),))
                else:
                    start_new_thread(self.udpSender, ('file error',))

            if comm[0] == 'playid':
                self.playlist_Refresh()

                file_path = os.path.abspath('./media/')
                file = os.path.join(file_path, self.playlist[comm[1]])
                print(file)
                if os.path.isfile(file):
                    mp.play(file)
                    start_new_thread(self.udpSender, ('play,{}'.format(comm[1]),))
                else:
                    start_new_thread(self.udpSender, ('file error',))
            

                

    def udpSender(self, msg):
        self.udpSendSock.sendto(msg.encode(), (rtIp, rtPort))
            

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
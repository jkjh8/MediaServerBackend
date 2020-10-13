# -*- coding: utf-8 -*-
import sys, vlc, socket, os.path, threading, json
from _thread import *
from time import sleep

instance = vlc.Instance()
player = instance.media_player_new()

setup = {}

class main_UdpServer():    
    def __init__(self):        
        port = 12302
        self.playlist = None
        self.udpSendSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('127.0.0.1', port))
        print("Udp Server Start {} : {}".format('127.0.0.1', port))

        self.setup_load()

    def playlist_Refresh(self):
        with open('playlist.json','r') as playlist_file:
            self.playlist = json.load(playlist_file)

    def setup_load(self):
        global setup
        with open('setup.json','r') as setupfile:
            setup = json.load(setupfile)
            print(setup['rtIp'])
            print(setup['rtPort'], type(setup['rtPort']))

    def setup_save(self):
        global setup
        with open('setup.json', 'w') as setupfile:
            json.dump(setup, setupfile)

    def run(self):
        while True:
            data, info = self.sock.recvfrom(65535)
            recv_Msg = data.decode()
            print(recv_Msg)
            self.dataParcing(recv_Msg)
            
    def dataParcing(self, data):
        global setup
        if data == "stop":
            mp.stop()
        elif data == "pause":
            mp.pause()
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

            elif comm[0] == 'playid':
                self.playlist_Refresh()
                if int(comm[1]) <= len(self.playlist):
                    file_path = os.path.abspath('./media/')
                    file = os.path.join(file_path, self.playlist[comm[1]])
                    print(file)
                    if os.path.isfile(file):
                        mp.play(file)
                        start_new_thread(self.udpSender, ('play,{}'.format(comm[1]),))
                    else:
                        start_new_thread(self.udpSender, ('file error',))
                else:
                    start_new_thread(self.udpSender, ('id is out of range',))
            
            elif comm[0] == 'returnIp':
                setup['rtIp'] = comm[1]
                setup['rtPort'] = int(comm[2])
                self.setup_save()
                start_new_thread(self.udpSender, ('returnAddr,{},{}'.format(setup['rtIp'], setup['rtPort']),))
            
            elif comm[0] == 'fullscreen':
                if comm[1] == 'true' or comm[1] == '1':
                    setup['fullscreen'] = True
                else:
                    setup['fullscreen'] = False
                mp.fullscreen()
                self.setup_save()

            elif comm[0] == 'progress':
                if comm[1] == 'true' or comm[1] == '1':
                    setup['progress'] = True
                else:
                    setup['progress'] = False
                self.setup_save()

            else:
                start_new_thread(self.udpSender, ('unknown command'),)


    def udpSender(self, msg):
        global setup
        self.udpSendSock.sendto(msg.encode(), (setup['rtIp'], setup['rtPort']))
            

class media_Player():
    global setup
    def __init__(self):
        self.mediafile = None
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

    def setNewPlayer(self):
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

    def setEventManager(self):
        global setup
        self.Event_Manager = self.player.event_manager()
        self.Event_Manager.event_attach(vlc.EventType.MediaPlayerEndReached, self.songFinished) #meida end
        self.Event_Manager.event_attach(vlc.EventType.MediaPlayerLengthChanged, self.getMediaLength, self.player) #media length
        self.Event_Manager.event_attach(vlc.EventType.MediaPlayerTimeChanged, self.getCurrentTime, self.player) #emdia get currnet time
    
    def setMedia(self, mediaFile):
        self.media = self.instance.media_new(mediaFile)
        self.player.set_media(self.media)

    def play(self, mediaFile):
        global setup    
        if mediaFile != self.mediafile:
            self.mediafile = mediaFile
            print(self.mediafile)
            if self.player.get_state().value != 1:
                print(self.player.get_state().value != 1)

            if not self.player:
                self.setNewPlayer()
                print("media player refresh")
            self.setEventManager()
            self.setMedia(self.mediafile)
            self.player.set_fullscreen(setup['fullscreen'])         
            self.player.play()
        else:
            self.pause()
    
    def pause(self):
        self.player.pause()

    def stop(self):
        self.mediafile = None
        self.player.stop()

    def fullscreen(self):
        status = self.player.get_state().value
        if status != 0:
            self.player.set_fullscreen(setup['fullscreen'])

    def songFinished(self,evnet):
        print("song Finish")
        start_new_thread(app.udpSender, ('end'),)

    def getMediaLength(self, time, player):
        sendTime = self.timeFormat(time.u.new_length)
        start_new_thread(app.udpSender, ('length,{}'.format(sendTime),))

    def getCurrentTime(self, time, player):
        global setup
        sendTime = self.timeFormat(time.u.new_time)
        if setup['progress']:
            start_new_thread(app.udpSender, ('current,{}'.format(sendTime),))

    def timeFormat(self, ms):
        time = ms/1000
        min, sec = divmod(time, 60)
        hour, min = divmod(min, 60)
        return ("%02d:%02d:%02d" % (hour, min, sec))


if __name__ == "__main__":
    mp = media_Player()
    app = main_UdpServer()
    app.run()
# -*- coding: utf-8 -*-
import sys, vlc, socket, os.path, threading, json
from _thread import *
from time import sleep

instance = vlc.Instance()
player = instance.media_player_new()

setup = {}
playlist = {}
MEDIA_PATH = os.path.abspath('./media/')

class main_UdpServer():    
    def __init__(self):        
        port = 12302
        self.playlist = None
        self.udpSendSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('127.0.0.1', port))
        print("Udp Server Start {} : {}".format('127.0.0.1', port))
        self.mp = media_Player()

        self.setup_load()

    def setup_load(self):
        global setup
        with open('setup.json','r') as setupfile:
            setup = json.load(setupfile)
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
            self.mp.stop()
        elif data == "pause":
            mp.pause()
        else:
            comm = data.split(',')
            if comm[0] == 'play':
                file = os.path.join(MEDIA_PATH, comm[1])
                print(file)
                if os.path.isfile(file):
                    mp.play(file)
                    start_new_thread(self.udpSender, ('play,{}'.format(comm[1]),))
                else:
                    start_new_thread(self.udpSender, ('file error',))

            elif comm[0] == 'playid':
                self.mp.playid(comm[1])

            elif comm[0] == 'returnIp':
                setup['rtIp'] = comm[1]; setup['rtPort'] = int(comm[2]); self.setup_save()
                start_new_thread(self.udpSender, ('returnAddr,{},{}'.format(setup['rtIp'], setup['rtPort']),))
            
            elif comm[0] == 'fullscreen':
                if comm[1] == 'true' or comm[1] == '1': setup['fullscreen'] = True
                else: setup['fullscreen'] = False
                self.mp.fullscreen(); self.setup_save()

            elif comm[0] == 'loop_one':
                if comm[1] == 'true' or comm[1] == '1': setup['loop_one'] = True
                else: setup['loop_one'] = False
                self.setup_save()
                start_new_thread(self.udpSender, ('loop_one,{}'.format(setup['loop_one']),))

            elif comm[0] == 'loop':
                if comm[1] == 'true' or comm[1] == '1': setup['loop_one'] = True
                else: setup['loop'] = False
                self.setup_save()
                start_new_thread(self.udpSender, ('loop,{}'.format(setup['loop']),))

            elif comm[0] == 'progress':
                if comm[1] == 'true' or comm[1] == '1': setup['progress'] = True
                else: setup['progress'] = False
                self.setup_save()

            else:
                start_new_thread(self.udpSender, ('unknown command'),)

    def udpSender(self, msg):
        global setup
        self.udpSendSock.sendto(msg.encode(), (setup['rtIp'], setup['rtPort']))
    
    def songFinished(self, play_id, play_file, play_list):
        self.mp.stop()
        print(play_id, play_file, play_list)
            

class media_Player():
    global setup
    def __init__(self):
        self.mediafile = None
        self.playlist = []
        self.play_id = None
        self.curr_time = None
        self.duration = None
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.setEventManager()

    def setNewPlayer(self):
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.setEventManager()

    def setEventManager(self):
        global setup
        self.Event_Manager = self.player.event_manager()
        self.Event_Manager.event_attach(vlc.EventType.MediaPlayerEndReached, self.songFinished) #meida end
        self.Event_Manager.event_attach(vlc.EventType.MediaPlayerLengthChanged, self.getMediaLength, self.player) #media length
        self.Event_Manager.event_attach(vlc.EventType.MediaPlayerTimeChanged, self.getCurrentTime, self.player) #emdia get currnet time
    
    def setMedia(self, mediaFile):
        print('SET',mediaFile)
        self.media = self.instance.media_new(mediaFile)
        self.player.set_media(self.media)

    def play(self, mediaFile):
        global setup
        if self.mediafile == mediaFile: self.player.stop()
        else: self.mediafile = mediaFile; self.setMedia(mediaFile)
        # print(mediaFile)
        # if self.player.get_state().value != 1:
        #     print(self.player.get_state().value != 1)
        # self.setNewPlayer() if (not self.player) else self.setNewPlayer(); print("media player refresh")
        start_new_thread(app.udpSender, ('play,{}'.format(self.mediafile),))
        
        self.player.set_fullscreen(setup['fullscreen'])         
        self.player.play()

    def playid(self, index):
        self.play_id = int(index)
        self.playlist = self.get_Playlist()

        if self.play_id <= len(self.playlist):
            file = self.playlist[self.play_id]['complete_name']
            if os.path.isfile(file):
                start_new_thread(app.udpSender, ('playid,{}'.format(index),))
                self.play(file)
            else:
                start_new_thread(app.udpSender, ('file_error',))            
        else:
            start_new_thread(app.udpSender, ('out_of_range',))
        
    def get_Playlist(self):
        with open('playlist.json','r') as playlist_file:
            return json.load(playlist_file)

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
        self.playlist = self.get_Playlist()
        start_new_thread(app.songFinished, (self.play_id,self.mediafile,self.playlist))
        self.curr_time = None
        self.duration = None
        
        start_new_thread(app.udpSender, ('end',))

    def getMediaLength(self, time, player):
        sendTime = self.timeFormat(time.u.new_length)
        if self.duration != sendTime:
            self.duration = sendTime
            start_new_thread(app.udpSender, ('length,{}'.format(sendTime),))

    def getCurrentTime(self, time, player):
        global setup
        if setup['progress']:
            sendTime = self.timeFormat(time.u.new_time)
            if self.curr_time != sendTime:
                self.curr_time = sendTime
                start_new_thread(app.udpSender, ('current,{}'.format(sendTime),))

    def timeFormat(self, ms):
        time = ms/1000
        min, sec = divmod(time, 60)
        hour, min = divmod(min, 60)
        return ("%02d:%02d:%02d" % (hour, min, sec))


if __name__ == "__main__":
    app = main_UdpServer()
    app.run()
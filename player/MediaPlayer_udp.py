# -*- coding: utf-8 -*-
import sys, vlc, socket, os.path, threading, json, tkinter
from ast import literal_eval
from _thread import *
from time import sleep

instance = vlc.Instance()
player = instance.media_player_new()

setup = {}
playlist = {}
port = 12302
MEDIA_PATH = os.path.abspath('./media/')


class main_UdpServer():    
    def __init__(self):
        self.playlist = None
        self.udpSendSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('127.0.0.1', port))
        print("Udp Server Start {} : {}".format('127.0.0.1', 12302))
        self.playlist_load()
        self.setup_load()
        self.mp = media_Player(self.setup)

    def setup_load(self):
        try:
            with open('setup.json','r') as setupfile:
                self.setup = json.load(setupfile)
        except:
            print('Setup file not found')
            self.setup = {}

    def setup_save(self):
        with open('setup.json', 'w') as setupfile:
            data = json.dump(self.setup, setupfile)

    def playlist_load(self):
        try:
            with open('playlist.json','r') as playlist_file:
                self.playlist = json.load(playlist_file)
        except:
            self.playlist = {}

    def run(self):
        while True:
            data, info = self.sock.recvfrom(65535)
            recv_Msg = data.decode()
            print(recv_Msg)
            self.dataParcing(recv_Msg)
            
    def dataParcing(self, data):
        try:

            if data == "stop":
                self.mp.stop()
                self.udpSender('stop')
            elif data == "pause":
                self.mp.pause()
                self.udpSender('pause')
            elif data == "getlist":
                list = []
                for item in self.playlist:
                    list.append(item['name'])
                self.udpSender('playlist,{}'.format(list))
            else:
                comm = data.split(',')
                if comm[0] == 'play':
                    self.play(comm[1])

                elif comm[0] == 'playid':
                    self.playid(int(comm[1]))

                elif comm[0] == 'returnip':
                    self.setup['rtIp'] = comm[1]; self.setup['rtPort'] = int(comm[2])
                    self.udpSender('returnAddr,{},{}'.format(self.setup['rtIp'], self.setup['rtPort']))
                
                elif comm[0] == 'fullscreen':
                    if comm[1] == 'true' or comm[1] == '1': self.setup['fullscreen'] = True
                    else: self.setup['fullscreen'] = False
                    self.mp.fullscreen();

                elif comm[0] == 'loop_one':
                    if comm[1] == 'true' or comm[1] == '1': self.setup['loop_one'] = True
                    else: self.setup['loop'] = False
                    self.udpSender('loop_one,{}'.format(self.setup['loop_one']))

                elif comm[0] == 'loop':
                    if comm[1] == 'true' or comm[1] == '1': self.setup['loop_one'] = True
                    else: self.setup['loop'] = False
                    self.udpSender('loop,{}'.format(self.setup['loop']))

                elif comm[0] == 'progress':
                    if comm[1] == 'true' or comm[1] == '1': self.setup['progress'] = True
                    else: self.setup['progress'] = False
                
                elif comm[0] == 'playlist':
                    self.playlist = json.loads(data.replace('playlist,','').replace("'",'"'))

                elif comm[0] == 'endclose':
                    if comm[1] == 'true' or comm[1] == '1': self.setup['endclose'] = True
                    else: self.setup['endclose'] = False
                else:
                    start_new_thread(self.udpSender, ('unknown command'),)
            self.setup_save()
        except Exception as e:
            print(e)

    def play(self, playfile):
        file = os.path.join(MEDIA_PATH, playfile)
        if os.path.isfile(file):
            self.mp.play(file)
            self.udpSender('play,{}'.format(playfile))
        else:
            self.udpSender('file error')

    def playid(self, playid):
        if playid < len(self.playlist):
            file = self.playlist[playid]['complete_name']
            if os.path.isfile(file):
                self.udpSender('playid,{}'.format(playid))
                self.play(file)
            else:
                self.udpSender('file_error')
        else:
            self.udpSender('out_of_playlist_range')

    def udpSender(self, msg):
        print(msg)
        print(self.setup['rtIp'], self.setup['rtPort'])
        self.udpSendSock.sendto(msg.encode(), (self.setup['rtIp'], self.setup['rtPort']))
    
    def songFinished(self, play_id, play_file, play_list):
        if self.setup['loop_one']:
            self.mp.playid(play_id)
            return
        elif self.setup['loop']:
            if play_id == len(play_list):
                play_id = 0
            else:
                play_id = play_id + 1
            self.mp.playid(play_id)
            return
        elif self.setup['endclose']:
            self.mp.stop()           

class media_Player():
    def __init__(self, setup):
        self.setup = setup
        self.windowthread = threading.Thread(target=self.create_window)
        self.windowthread.start()
        self.mediafile = None
        self.curr_time = None
        self.duration = None
        self.setNewPlayer()

    def setNewPlayer(self):
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.player.set_hwnd(self.window.winfo_id())
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
        print('SET',mediaFile)
        self.media = self.instance.media_new(mediaFile)
        self.player.set_media(self.media)

    def play(self, mediaFile):
        if self.mediafile == mediaFile: self.player.stop()
        else: self.mediafile = mediaFile; self.setMedia(mediaFile)
        app.udpSender('play,{}'.format(self.mediafile))
        try:
            self.window.attributes("-fullscreen", self.setup['fullscreen'])
        except:
            self.window.attributes("-fullscreen", True)
        self.player.play()

    def pause(self):
        self.player.pause()

    def stop(self):
        self.mediafile = None
        self.player.stop()

    def fullscreen(self):
        try:
            self.window.attributes("-fullscreen", self.setup['fullscreen'])
            
        except:
            self.window.attributes("-fullscreen", True)

    def songFinished(self,evnet):
        self.playlist = self.get_Playlist()
        start_new_thread(app.songFinished, (self.play_id, self.mediafile, self.playlist))
        self.curr_time = None
        self.duration = None
        
        start_new_thread(app.udpSender, ('end',))

    def getMediaLength(self, time, player):
        sendTime = self.timeFormat(time.u.new_length)
        if self.duration != sendTime:
            self.duration = sendTime
            start_new_thread(app.udpSender, ('length,{}'.format(sendTime),))

    def getCurrentTime(self, time, player):
        if app.setup['progress']:
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
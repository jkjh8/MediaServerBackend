from flask import Flask, jsonify, request, render_template
from flask_socketio import SocketIO, send, emit
from flask_cors import CORS
from werkzeug.utils import secure_filename
from pymediainfo import MediaInfo

import os, socket, json

playServerIP = "127.0.0.1"
playServerPort = 12302

udpSendSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
MEDIA_DIR = os.path.join(BASE_DIR,'media')

# instantiate the app
app = Flask(__name__)
app.secret_key = "secret"
socketio = SocketIO(app, cors_allowed_origins="*")

# enable CORS
CORS(app, resources={r'/*': {'origins': '*'}})

# sanity check route
@app.route('/', methods=['GET'])
def test_router():
    return render_template('index.html')

@app.route('/player', methods=['post'])
def play_command():
    data = request.get_json()
    command = data['command']
    if command == "play":
        file = data['file']
        udpSender("{},{}".format(command,file))
    else:
        udpSender(command)
    return jsonify(command)

@app.route('/upload', methods = ['POST'])
def upload_file():
    f = request.files['file']
    f.save(os.path.join(MEDIA_DIR, f.filename))
    return jsonify(success=True)

@app.route('/getSetup', methods = ['GET'])
def get_setup():
    return jsonify(loadfile_setup())

@app.route('/getFileList', methods = ['GET'])
def refresh_files():
    return jsonify(getMediaFileData())

@app.route('/setPlayList', methods = ['POST'])
def setPlayList():
    data = request.get_json()
    savefile_playlist(data)
    socket_get_playlist(data)
    udpSender('playlist,{}'.format(data))
    return jsonify(success=True)

@app.route('/getPlayList', methods = ['GET'])
def getPlayList():
    return jsonify(loadfile_playlist())

@app.route('/playlistrefresh', methods = ['GET'])
def PlayListFresh():
    play_list = compare_playlist()
    savefile_playlist(play_list)
    return (jsonify(play_list))

def loadfile_setup():
    with open('..setup.json', 'r') as setupfile:
        setup = json.load(setupfile)
    return (setup)

def loadfile_playlist():
    with open('../playlist.json', 'r') as playlistfile:
        playList = json.load(playlistfile)
    return (playList)

def compare_playlist():
    play_list = loadfile_playlist()
    fileNameList = os.listdir(MEDIA_DIR)
    for file in play_list:
        if os.path.basename(file['complete_name']) not in fileNameList:
            print(file)
            play_list.remove(file)
    return(play_list)

@app.route('/removeFile', methods = ['POST'])
def remove_file():
    data = request.get_json()
    file = data['file']    
    if os.path.isfile(file):
        os.remove(file)
    savefile_playlist(compare_playlist())
    fileList = getMediaFileData()
    socket_get_filelist(fileList)    
    return jsonify(fileList)

def savefile_playlist(playlist):
    with open('../playlist.json', 'w') as playlistfile:
        json.dump(playlist, playlistfile)

def getMediaFileData():
    fileList = []
    fileNameList = os.listdir(MEDIA_DIR)
    for item in fileNameList:
        fileInfo = {}
        info = MediaInfo.parse(os.path.join(MEDIA_DIR,item)).tracks[0]
        fileInfo['name'] = info.file_name
        fileInfo['complete_name'] = info.complete_name
        fileInfo['type'] = info.file_extension
        fileInfo['size'] = info.file_size
        fileInfo['duration'] = info.duration
        fileList.append(fileInfo)
    return(fileList)

def socket_get_playlist(data):
    socketio.emit('playlist', data)

def socket_get_filelist(data):
    socketio.emit('filelist', data)

def socket_get_player_setup(data):
    socketio.emit('playersetup', data)

@socketio.on('filelist')
def socket_Get_File_list_Call():
    print('list')
    data = getMediaFileData()
    emit('filelist', data, broadcast=True)

@socketio.on('message')
def handle_message(message):
    send("ok MSG")

def udpSender(msg):
    try:
        udpSendSock.sendto(msg.encode(), (playServerIP, playServerPort))
    except Exception as e:
        print('error : ', e)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0',port=12300, debug=True)
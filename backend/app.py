from flask import Flask, jsonify, request, render_template, _app_ctx_stack, Response
from flask_socketio import SocketIO, send, emit
from flask_cors import CORS
# from pymediainfo import MediaInfo
from flask_pymongo import PyMongo
from mediainfo import FileMediaInfo
import os, socket, json, threading, datetime, netifaces, time

playServerIP = "127.0.0.1"
playServerPort = 12302

udpSendSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
MEDIA_DIR = os.path.join(BASE_DIR,'media')
print(MEDIA_DIR)

# instantiate the app
app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/MediaServer"
app.config['SECRET_KEY'] = 'sdfkhK#k2!uds#^j&3cf#es*327193%^12902)'
app.config['TESTING'] = True
app.config['JSON_AS_ASCII'] = True
CORS(app, resources={r'/*': {'origins': '*'}})
socketio = SocketIO(app, cors_allowed_origins="*")
mongo = PyMongo(app)
db = mongo.db

FileMediaInfo(mongo.db.filelist, MEDIA_DIR)

def getip():    
    netifaces.ifaddresses('eno2')
    IP =  netifaces.ifaddresses('eno2')[netifaces.AF_INET][0]['addr']
    return IP

# sanity check route
@app.route('/', methods=['GET'])
def test_router():
    # time.sleep(3)
    ip = getip()
    return ip

@app.route('/player', methods=['post'])
def play_command():
    data = request.get_json()
    command = data['command']
    if command == "play":
        file = data['file']
        udpSender("{},{}".format(command,file))
    else:
        udpSender(command)
    socket_get_ip()
    return jsonify(command)

@app.route('/upload', methods = ['POST'])
def upload_file():
    f = request.files['file']
    f.save(os.path.join(MEDIA_DIR, f.filename))
    FileMediaInfo(mongo.db.filelist, MEDIA_DIR)
    soket_get_filelist()
    return jsonify(success=True)

@app.route('/setup', methods = ['GET','POST'])
def setup():
    if request.method == 'POST':
        data = request.get_json()
        db.setup.save(data)
        socket_get_player_setup()
    udpSender('refresh')
    return jsonify(db.setup.find_one())

@app.route('/filelist', methods = ['GET'])
def refresh_files():
    files = list(db.filelist.find({},{ '_id': False }))
    print(files)
    return jsonify(files)

@app.route('/playlist', methods = ['GET','POST'])
def playlist():
    if request.method == 'POST':
        data = request.get_json()
        update_playlist(data)
        # socket_get_playlist()
    files = list(db.playlist.find({},{ '_id': False }))
    socket_get_ip()
    # return json.dumps(files, default=json_util.default)
    return jsonify(files)

@app.route('/compare')
def compare_playlist():
    play_list = list(db.playlist.find({},{ '_id': False }))
    file_list = list(db.filelist.find({},{ '_id': False }))
    for file in play_list:
        if not db.filelist.find_one({ 'complete_name': file['complete_name'] }):
            db.playlist.delete_one({ 'complete_name': file['complete_name'] })
    return '200'
    # return(play_list)

@app.route('/removeFile', methods = ['POST'])
def remove_file():
    file = request.get_json()['file']
    if os.path.isfile(file):
        print(file)
        os.remove(file)
        db.filelist.delete_one({ 'complete_name': file })
    # getMediaFileFromDisk()
    files = list(db.filelist.find({},{ '_id': False }))
    return jsonify(files)

def update_playlist(playlist):
    print(playlist)
    db.playlist.delete_many({})
    files = []
    for idx, item in enumerate(playlist):
        item['playid'] = idx
        files.append(item)
    db.playlist.insert_many(files)

@socketio.on('filelist')
def soket_get_filelist():
    print('filelist send')
    files = list(db.filelist.find({},{ '_id': False }))
    socketio.emit('filelist', files, broadcast=True)

@socketio.on('playlist')
def socket_get_playlist():
    files = list(db.playlist.find({},{ '_id': False }))
    socketio.emit('playlist', files, broadcast=True)

@socketio.on('setup')
def socket_get_player_setup():
    print('setup send')
    setup = db.setup.find_one()
    setup['_id'] = str(setup['_id'])
    print(setup)
    socketio.emit('setup', setup, broadcast=True)

@socketio.on('getip')
def socket_get_ip():
    ip = getip()
    print(ip)
    socketio.emit('getip', ip, broadcast=True)

def udpSender(msg):
    try:
        udpSendSock.sendto(msg.encode(), (playServerIP, playServerPort))
    except Exception as e:
        print('error : ', e)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=12300, debug=True)
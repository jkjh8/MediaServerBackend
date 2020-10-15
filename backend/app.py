from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename

import os, socket, json

playServerIP = "127.0.0.1"
playServerPort = 12302

udpSendSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# instantiate the app
app = Flask(__name__)

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
        print(file)
        udpSender("{},{}".format(command,file))
    else:
        udpSender(command)
    return jsonify(command)

@app.route('/upload', methods = ['POST'])
def upload_file():
    f =request.files['file']
    f.save(os.path.join('../media/', secure_filename(f.filename)))
    file_list = os.listdir('../media/')
    return jsonify(file_list)

@app.route('/getFileList', methods = ['GET'])
def refresh_files():
    file_list = os.listdir('../media/')
    return jsonify(file_list)

@app.route('/setPlayList', methods = ['POST'])
def setPlayList():
    data = request.get_json()
    playList = data['playList']
    dict_playlist = {i:playList[i] for i in range(len(playList))}
    with open('../playlist.json', 'w') as playlistfile:
        json.dump(dict_playlist, playlistfile)
    return jsonify(playList)

@app.route('/getPlayList', methods = ['GET'])
def getPlayList():
	with open('../playlist.json', 'r') as playlistfile:
		playList = json.load(playlistfile)
	playList = list(playList.values())
	return jsonify(playList)

def udpSender(msg):
    udpSendSock.sendto(msg.encode(), (playServerIP, playServerPort))

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=12300, debug=True)
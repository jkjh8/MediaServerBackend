from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

import os, socket

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

    return jsonify('This is Docker Test developments Server!')

@app.route('/play', methods=['post'])
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

@app.route('/refresh')
def refresh_files():
    file_list = os.listdir('../media/')
    return jsonify(file_list)


def udpSender(msg):
    udpSendSock.sendto(msg.encode(), (playServerIP, playServerPort))

if __name__ == '__main__':
    app.run(debug=True)
# Original Author       : Ghasem Abdi, ghasem.abdi@yahoo.com
# File Last Update Date : December 12, 2022

from flask import Flask, request
from flask_socketio import SocketIO, send

# Create a Flask instance
app = Flask(__name__)
socketio = SocketIO(app)


# Use the route() decorator to tell Flask what URL should trigger our function
@app.route('/', methods=['POST'])
def post():
    data = request.get_data()
    send(data, namespace='/', broadcast=True)
    return data, 201


# Start the web server
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

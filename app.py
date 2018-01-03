from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from pymodm.errors import DoesNotExist
from model import User


async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
app.debug = True
socketio = SocketIO(app, async_mode=async_mode)


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        return render_template('index.html', async_mode=socketio.async_mode, username=str(request.form.get('username')))


@socketio.on('my_connect', namespace='/chat')
def handle_connect(message):
    print('Inside handle_connect --> message: ', message, ' --> SID:', request.sid)
    try:
        user = User.objects.raw({'username': message['username']})
        result = user.update({'$set': {'current_sid': request.sid}})
        if result == 0:
            User(message['username'], request.sid).save()
    except DoesNotExist as err:
        print('handle_connect --> User does not exists for username: ', message['username'], '--> ', err)
        User(message['username'], request.sid).save()

    emit('response', {'data': message['data']})


@socketio.on('broadcast_event', namespace='/chat')
def handle_broadcast_event(message):
    print('Inside handle_broadcast_event --> message: ', message)
    emit('response', {'data': message['data']}, broadcast=True)


@socketio.on('chat_event', namespace='/chat')
def handle_chat_event(message):
    print('Inside handle_chat_event --> message: ', message)
    username = message['username']
    recipient = message['recipient']
    data = message['data']

    try:
        recipient_user = User.objects.get({'username': recipient})
        if recipient_user:
            emit('response', {'data': data, 'sender': username}, room=recipient_user.current_sid)
        else:
            emit('response', {'data': 'User ' + recipient + ' does not Exist\'s'}, room=request.sid)
    except DoesNotExist as err:
        print('handle_chat_event --> Recipient does not exists: ', recipient)
        emit('response', {'data': 'User ' + recipient + ' does not Exist\'s'}, room=request.sid)


if __name__ == '__main__':
    socketio.run(app)

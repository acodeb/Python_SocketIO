from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, disconnect
from pymodm.errors import DoesNotExist
from model import User, History


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
    emit('response', {'data': message['data'], 'broadcast': True}, broadcast=True)


@socketio.on('load_history', namespace='/chat')
def load_history(username):
    print('Inside Load_history --> Username: ', username)
    try:
        messages = []
        user_history = History.objects.raw({'$or': [{'sender': username}, {'recipient': username}]})
        for history in user_history:
            messages.append({'data': history.message, 'sender': history.sender})
        emit('load_history_response', {'messages': messages}, room=request.sid)
    except DoesNotExist as err:
        print('load_history --> No History for user {}'.format(username), ' -->', err)


@socketio.on('chat_event', namespace='/chat')
def handle_chat_event(message):
    print('Inside handle_chat_event --> message: ', message)
    username = message['username']
    recipient = message['recipient']
    data = message['data']

    try:
        recipient_user = User.objects.get({'username': recipient})
        if recipient_user:
            History(username, recipient, data).save()
            emit('response', {'data': data, 'sender': username}, room=recipient_user.current_sid)
        else:
            emit('response', {'data': 'User ' + recipient + ' is not Available'}, room=request.sid)
    except DoesNotExist as err:
        print('handle_chat_event --> Recipient does not exists: ', recipient, ' -->', err)
        emit('response', {'data': 'User ' + recipient + ' does not Exist\'s'}, room=request.sid)


@socketio.on('logout_event', namespace='/chat')
def handle_logout():
    print('Inside handle_logout -->')
    emit('logout_response', room=request.sid)
    disconnect()


if __name__ == '__main__':
    socketio.run(app)

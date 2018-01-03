from pymodm import connect, fields, MongoModel

connect('mongodb://localhost:27017/socketio')


class User(MongoModel):
    username = fields.CharField()
    current_sid = fields.CharField()


class History(MongoModel):
    message = fields.CharField()

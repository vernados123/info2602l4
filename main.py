import json
from flask import Flask, request
from flask_cors import CORS
from flask_jwt import JWT, jwt_required, current_identity
from sqlalchemy.exc import IntegrityError
from datetime import timedelta 

from models import db, User, Todo

# Complete Lab 5

''' Begin boilerplate code '''
def create_app():
  app = Flask(__name__, static_url_path='')
  app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
  app.config['SECRET_KEY'] = "MYSECRET"
  app.config['JWT_EXPIRATION_DELTA'] = timedelta(days = 7) 
  CORS(app)
  db.init_app(app)
  return app

app = create_app()

app.app_context().push()
db.create_all(app=app)
''' End Boilerplate Code '''

''' Set up JWT here '''
def authenticate(uname, password):
  #search for the specified user
  user = User.query.filter_by(username=uname).first()
  #if user is found and password matches
  if user and user.check_password(password):
    return user

#Payload is a dictionary which is passed to the function by Flask JWT
def identity(payload):
  print(payload)
  return User.query.get(payload['identity'])

jwt = JWT(app, authenticate, identity)

''' End JWT Setup '''


@app.route('/', methods=['GET'])
def index():
 return app.send_static_file('index.html')


@app.route('/signup', methods=['POST'])
def signup():
  userdata = request.get_json() # get userdata
  newuser = User(username=userdata['username'], email=userdata['email']) # create user object
  newuser.set_password(userdata['password']) # set password
  try:
    db.session.add(newuser)
    db.session.commit() # save user
  except IntegrityError: # attempted to insert a duplicate user
    db.session.rollback()
    return 'username or email already exists' # error message
  return 'user created' # success

@app.route('/identify')
@jwt_required()
def protected():
    return json.dumps(current_identity.username)

@app.route('/todo', methods=['POST'])
@jwt_required()
def create_todo():
  data = request.get_json()
  todo = Todo(text=data['text'], userid=current_identity.id, done=False)
  db.session.add(todo)
  db.session.commit()
  return json.dumps(todo.id), 201 # return data and set the status code

@app.route('/todo', methods=['GET'])
@jwt_required()
def get_todos():
  todos = Todo.query.filter_by(userid=current_identity.id).all()
  todos = [todo.toDict() for todo in todos] # list comprehension which converts todo objects to dictionaries
  return json.dumps(todos)

@app.route('/todo/<id>', methods=['GET'])
@jwt_required()
def get_todo(id):
  todo = Todo.query.filter_by(userid=current_identity.id, id=id).first()
  if todo == None:
    return 'Invalid id or unauthorized'
  return json.dumps(todo.toDict())

@app.route('/todo/<id>', methods=['PUT'])
@jwt_required()
def update_todo(id):
  todo = Todo.query.filter_by(userid=current_identity.id, id=id).first()
  if todo == None:
    return 'Invalid id or unauthorized'
  data = request.get_json()
  if 'text' in data: # we can't assume what the user is updating wo we check for the field
    todo.text = data['text']
  if 'done' in data:
    todo.done = data['done']
  db.session.add(todo)
  db.session.commit()
  return 'Updated', 201

@app.route('/todo/<id>', methods=['DELETE'])
@jwt_required()
def delete_todo(id):
  todo = Todo.query.filter_by(userid=current_identity.id, id=id).first()
  if todo == None:
    return 'Invalid id or unauthorized'
  db.session.delete(todo) # delete the object
  db.session.commit()
  return 'Deleted', 204

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080, debug=True)
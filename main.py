from flask import Flask, request, jsonify
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
  app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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
    return jsonify({ "error" : "username or email already exists"}) # error message
  return jsonify({ "message" : "user created"}) # success

@app.route('/identify')
@jwt_required()
def protected():
  user = User.query.get(current_identity.id)
  return jsonify(user.toDict())

@app.route('/users', methods=['GET'])
def get_users():
  users = User.query.all()
  users_list = [ user.toDict() for user in users ] 
  # convert user objects to list of dictionaries
  return jsonify({ "num_users": len(users_list), "users": users_list })

@app.route('/todos', methods=['POST'])
@jwt_required()
def create_todo():
  data = request.get_json()
  todo = Todo(text=data['text'], userid=current_identity.id, done=False)
  db.session.add(todo)
  db.session.commit()
  return jsonify({ 'id' : todo.id}), 201 # return data and set the message code

@app.route('/todos', methods=['GET'])
@jwt_required()
def get_todos():
  todos = Todo.query.filter_by(userid=current_identity.id).all()
  todos = [todo.toDict() for todo in todos] # list comprehension which converts todo objects to dictionaries
  return jsonify(todos)

@app.route('/todos/<id>', methods=['GET'])
@jwt_required()
def get_todo(id):
  todo = Todo.query.filter_by(userid=current_identity.id, id=id).first()
  if todo == None:
    return jsonify({'error':'Invalid id or unauthorized'})
  return jsonify(todo.toDict())

@app.route('/todos/<id>', methods=['PUT'])
@jwt_required()
def update_todo(id):
  todo = Todo.query.filter_by(userid=current_identity.id, id=id).first()
  if todo == None:
    return jsonify({'error':'Invalid id or unauthorized'})
  data = request.get_json()
  if 'text' in data: # we can't assume what the user is updating so we check for the field
    todo.text = data['text']
  if 'done' in data:
    todo.done = data['done']
  db.session.add(todo)
  db.session.commit()
  return jsonify({'message':'Updated'}), 201

@app.route('/todos/<id>', methods=['DELETE'])
@jwt_required()
def delete_todo(id):
  todo = Todo.query.filter_by(userid=current_identity.id, id=id).first()
  if todo == None:
    return 'Invalid id or unauthorized'
  db.session.delete(todo) # delete the object
  db.session.commit()
  return jsonify({'message':'Deleted'}), 200

@app.route('/stats/todos', methods=['GET'])
@jwt_required()
def get_todo_stats():
  user = User.query.get(current_identity.id)
  if user:
    return jsonify({
      "num_todos": user.get_num_todos(),
      "num_done": user.get_done_todos()
    })
  else :
    return jsonify({'message': 'User not found'}), 404


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080, debug=True)

from flask import Flask, jsonify, request, flash, render_template, redirect, url_for, Response, make_response
from functools import wraps
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
    set_access_cookies,
    unset_jwt_cookies,
    current_user
)

from models import Admin, Category, RegularUser, Todo, TodoCategory, db, User

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'MySecretKey'
app.config['JWT_ACCESS_COOKIE_NAME'] = 'access_token'
app.config['JWT_REFRESH_COOKIE_NAME'] = 'refresh_token'
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_SECURE"] = True
app.config["JWT_SECRET_KEY"] = "super-secret"
app.config["JWT_COOKIE_CSRF_PROTECT"] = False

db.init_app(app)
app.app_context().push()

jwt = JWTManager(app)


# Auth Setup
# custom decorator authorize routes for admin or regular user
def login_required(required_class):
  def wrapper(f):
      @wraps(f)
      @jwt_required()  # Ensure JWT authentication
      def decorated_function(*args, **kwargs):
        user = required_class.query.filter_by(username=get_jwt_identity()).first()  
        print(user.__class__, required_class, user.__class__ == required_class)
        if user.__class__ != required_class:  # Check class equality
            return jsonify(message='Invalid user role'), 403
        return f(*args, **kwargs)
      return decorated_function
  return wrapper

@jwt.user_identity_loader
def user_identity_lookup(user):
  return user.id


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
  identity = jwt_data["sub"]
  return User.query.get(identity)


@jwt.unauthorized_loader
@jwt.invalid_token_loader
def custom_unauthorized_response(error):
    return render_template('401.html', error=error), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return render_template('401.html'), 401  

# ******************************************************************

def login_user(username, password):
  user = User.query.filter_by(username=username).first()
  if user and user.check_password(password):
    token = create_access_token(identity=user)
    return token
  return None


# View Routes

@app.route('/', methods=['GET'])
@app.route('/login', methods=['GET'])
def login_page():
  return render_template('login.html')


@app.route('/app', methods=['GET'])
@jwt_required()
def todos_page():
  return render_template('todo.html', todos=current_user.todos, current_user=current_user)


@app.route('/signup', methods=['GET'])
def signup_page():
  return render_template('signup.html')


@app.route('/editTodo/<id>', methods=["GET"])
@jwt_required()
def edit_todo_page(id):
  todos = Todo.query.all()
  todo = Todo.query.filter_by(id=id, user_id=current_user.id).first()
  if todo:
    return render_template('edit.html', todo=todo, current_user=current_user)
  flash('Todo not found or unauthorized')
  return redirect(url_for('todos_page'))


# Action Routes

@app.route('/logout', methods=['GET'])
@jwt_required()
def logout_action():
  flash('Logged Out')
  response = make_response(redirect(url_for('login_page')))
  unset_jwt_cookies(response)
  return response


if __name__ == "__main__":
  app.run(host='0.0.0.0', port=81)

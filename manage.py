from main import db, User, Todo

def create_user(username, email, password):
    newuser = User(username=username, email=email) # create user object
    newuser.set_password(password) # set password
    db.session.add(newuser)
    db.session.commit()

def create_todo(text, username):
    user = User.query.filter_by(username=username).first()
    if user:
        todo = Todo(text=text, userid=user.id, done=False)
        db.session.add(todo)
        db.session.commit()
        print('Todo created!')
    else:
        print('Todo not created, user not found')

create_todo('washcar', 'bob')
create_todo('do laundry', 'bob')


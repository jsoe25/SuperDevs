# imports
import os
from flask import Flask  # Flask is the web app that we will customize
from flask import render_template
from flask import request
from flask import redirect, url_for
from database import db
from models import Project as Project
from models import Task as Task
from models import User as User
from forms import RegisterForm
from forms import LoginForm
from forms import TaskForm
from flask import session
import bcrypt

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flask_project_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'SE3155'
# Bind SQLAlchemy db object to this Flask app
db.init_app(app)
# setup models
with app.app_context():
    db.create_all()


@app.route('/')
@app.route('/index')
def index():
    # check if a user is saved in the session
    if session.get('user'):
        return  render_template('index.html', user=session['user'])
    return render_template('index.html')


@app.route('/projects')
def get_projects():
    # check if a user is saved in the session
    if session.get('user'):
        # get projects from database
        projects = db.session.query(Project).all()
        return render_template('projects.html', projects=projects, user=session['user'])
    else:
        return redirect(url_for('login'))


@app.route('/projects/<project_id>')
def get_tasks(project_id):
    # check if a user is saved in the session
    if session.get('user'):
        # get project from database
        projects = db.session.query(Project).filter_by(id=project_id).one()
        projects.counter += 1
        # set up a task form
        tasks = TaskForm()
        db.session.add(projects)
        db.session.commit()
        return render_template('tasks.html', projects=projects, user=session['user'], form=tasks)
    else:
        return redirect(url_for('login'))


@app.route('/projects/newProject', methods=['GET', 'POST'])
def new_project():
    # check if a user is saved in the session
    if session.get('user'):
        # check method used for request
        if request.method == 'POST':
            # get title data
            title = request.form['title']
            # get note data
            text = request.form['projectText']
            # create date stamp
            from datetime import date
            today = date.today()
            # format date mm/dd/yyyy
            today = today.strftime("%m-%d-%Y")
            counter = 0
            new_record = Project(title, text, today, counter, session['user_id'])
            db.session.add(new_record)
            db.session.commit()
            return redirect(url_for('get_projects'))
        else:
            return render_template("newProject.html", user=session['user'])
    else:
        return redirect(url_for('login'))


@app.route('/projects/newTask/<project_id>', methods=['POST'])
def new_task(project_id):
    # check if a user is saved in the session
    if session.get('user'):
        task_form = TaskForm()
        if task_form.validate_on_submit():
            task_title = request.form['task']
            new_record = Task(task_title, project_id, session['user'])
            db.session.add(new_record)
            db.session.commit()
        return redirect(url_for('get_tasks', project_id=project_id))
    else:
        return redirect(url_for('login'))


@app.route('/projects/edit/<project_id>', methods=['GET', 'POST'])
def update_project(project_id):
    if request.method == 'POST':
        title = request.form['title']
        text = request.form['projectText']
        project = db.session.query(Project).filter_by(id=project_id).one()
        project.title = title
        project.text = text
        db.session.add(project)
        db.session.commit()
        return redirect(url_for('get_projects'))
    else:
        a_user = db.session.query(User).filter_by(email='mogli@uncc.edu')
        my_project = db.session.query(Project).filter_by(id=project_id).one()
        return render_template('newProject.html', project=my_project, user=a_user)


@app.route('/projects/delete/<project_id>', methods=['POST'])
def delete_project(project_id):
    my_project = db.session.query(Project).filter_by(id=project_id).one()
    db.session.delete(my_project)
    db.session.commit()
    return redirect(url_for('get_projects'))


# does not work and we can't figure out why
@app.route('/projects/tasks/<task_id>/delete', methods=['POST'])
def delete_task(task_id):
    # task = db.session.query(Task).filter_by(id=task_id).one()

    task = Task.query.filter(Task.id == task_id).first()
    db.session.delete(task)
    db.session.commit()
    return render_template('tasks.html', task=task_id)

@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    if request.method == 'POST' and form.validate_on_submit():
        # salt and hash password
        h_password = bcrypt.hashpw(
            request.form['password'].encode('utf-8'), bcrypt.gensalt())
        # get entered user data
        first_name = request.form['firstname']
        last_name = request.form['lastname']
        # create user model
        new_user = User(first_name, last_name, request.form['email'], h_password)
        # add user to database and commit
        db.session.add(new_user)
        db.session.commit()
        # save the user's name to the session
        session['user'] = first_name
        session['user_id'] = new_user.id  # access id value from user model of this newly added user
        # show user dashboard view
        return redirect(url_for('get_projects'))

    # something went wrong - display register view
    return render_template('signup.html', form=form)


@app.route('/login', methods=['POST', 'GET'])
def login():
    login_form = LoginForm()
    # validate_on_submit only validates using POST
    if login_form.validate_on_submit():
        # we know user exists. We can use one()
        the_user = db.session.query(User).filter_by(email=request.form['email']).one()
        # user exists check password entered matches stored password
        if bcrypt.checkpw(request.form['password'].encode('utf-8'), the_user.password):
            # password match add user info to session
            session['user'] = the_user.first_name
            session['user_id'] = the_user.id
            # render view
            return redirect(url_for('get_projects'))

        # password check failed
        # set error message to alert user
        login_form.password.errors = ["Incorrect username or password."]
        return render_template("login.html", form=login_form)
    else:
        # form did not validate or GET request
        return render_template("login.html", form=login_form)

@app.route('/logout')
def logout():
    # check if a user is saved in session
    if session.get('user'):
        session.clear()

    return redirect(url_for('index'))


@app.get("/toggle-theme")
def toggle_theme():
    current_theme = session.get("theme")
    if current_theme == "dark":
        session["theme"] = "light"
    else:
        session["theme"] = "dark"
    return redirect(request.args.get("current_page"))

@app.get("/faq")
def faq():
    selected_question = request.args.get('type')
    if selected_question == "question1":
        return render_template('index.html', Answer='Chello is meant to help teams create projects and tasks for those projects created.')
    elif selected_question == "question2":
        return render_template('index.html', Answer='Chello is always changing and will continue to add new features focused on improving usability and effectivness between teams.')
    elif selected_question == "question3":
        return render_template('index.html', Answer='Chello allows for the ability to add images to a project/task, you can also change your theme between light and dark.')
    else:
        return render_template('index.html', Answer='')






app.run(host=os.getenv('IP', '127.0.0.1'), port=int(os.getenv('PORT', 5000)), debug=True)
# To see the web page in your web browser, go to the url,
#   http://127.0.0.1:5000
#   http://127.0.0.1:5000/index
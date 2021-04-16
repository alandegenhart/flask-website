"""Authentication module"""

import functools
import flask
import werkzeug.security
import profile.db


bp = flask.Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    """Register a user."""
    # Handle post request to registration page
    if flask.request.method == 'POST':
        # Get submitted username and password
        username = flask.request.form['username']
        password = flask.request.form['password']
        db = profile.db.get_db()
        error = None

        # Error checking -- make sure username and password are not empty and
        # that the user does not exist
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required'
        elif db.execute(
            'SELECT id FROM user WHERE username = ?', (username, )
        ).fetchone() is not None:
            error = f'User {username} is already registered.'

        # If there was not an error, create the user
        if error is None:
            query = 'INSERT INTO user (username, password) VALUES (?, ?)'
            db.execute(query, (username, werkzeug.security.generate_password_hash(password)))
            db.commit()
            return flask.redirect(flask.url_for('auth.login'))  # 'auth.login' is (blueprint name).(view function name)

        flask.flash(error)

    return flask.render_template('auth/register.html')  # Path to template


@bp.route('/login', methods=('GET', 'POST'))
def login():
    """Log in a user."""
    # Handle post request
    if flask.request.method == 'POST':
        # Get submitted username and password and query the database
        username = flask.request.form['username']
        password = flask.request.form['password']
        db = profile.db.get_db()
        error = None
        query = 'SELECT * FROM user WHERE username = ?'
        user = db.execute(query, (username,)).fetchone()

        # Check user and password
        if user is None:
            error = 'Username not found.'
        elif not werkzeug.security.check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            # Login info is correct -- clear the current session, create a new
            # one for the current user, and redirect to the home page
            flask.session.clear()
            flask.session['user_id'] = user['id']
            return flask.redirect(flask.url_for('home'))

        flask.flash(error)

    return flask.render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = flask.session.get('user_id')

    if user_id is None:
        flask.g.user = None
    else:
        # If a user is successfully logged in, get their info
        query = 'SELECT * FROM user WHERE id = ?'
        flask.g.user = profile.db.get_db().execute(query, (user_id,)).fetchone()


@bp.route('/logout')
def logout():
    """Log out the current user"""
    flask.session.clear()
    return flask.redirect(flask.url_for('home'))


def login_required(view):
    """A decorator used to require a user be logged in"""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if flask.g.user is None:
            # If the user is none, redirect
            return flask.redirect(flask.url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

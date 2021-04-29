"""Authentication module"""

import functools
import flask
import werkzeug.security
import profile.db


bp = flask.Blueprint('admin', __name__, url_prefix='/admin')


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
            return flask.redirect(flask.url_for('admin.login'))  # 'admin.login' is (blueprint name).(view function name)

        flask.flash(error)

    return flask.render_template('admin/register.html')  # Path to template


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
            return flask.redirect(flask.url_for('admin.dashboard'))

        flask.flash(error)

    return flask.render_template('admin/login.html')


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
            return flask.redirect(flask.url_for('admin.login'))

        return view(**kwargs)

    return wrapped_view


@bp.route('/')
@login_required
def dashboard():
    """Main dashboard view for management."""
    # TODO -- get overview data here
    return flask.render_template('admin/dashboard.html')


@bp.route('/users')
@login_required
def users():
    """Display list of users"""
    query = 'SELECT id, username FROM user ORDER BY id'
    rows = profile.db.get_db().execute(query).fetchall()
    table_data = {
        'table_title': 'Users',
        'table_name': 'user',
        'rows': rows
    }
    return flask.render_template('admin/display_table.html', table_data=table_data)


@bp.route('/posts')
@login_required
def posts():
    """Display list of posts"""
    query = 'SELECT id, author_id, created, title FROM post ORDER BY id'
    rows = profile.db.get_db().execute(query).fetchall()
    table_data = {
        'table_title': 'Posts',
        'table_name': 'post',
        'rows': rows
    }
    return flask.render_template('admin/display_table.html', table_data=table_data)


@bp.route('/publications')
@login_required
def publications():
    """Display list of publications"""
    query = 'SELECT id, type, year, title, journal FROM publication ORDER BY id'
    rows = profile.db.get_db().execute(query).fetchall()
    table_data = {
        'table_title': 'Publications',
        'table_name': 'publication',
        'rows': rows
    }
    return flask.render_template('admin/display_table.html', table_data=table_data)


@bp.route('/create-user', methods=('GET', 'POST'))
@login_required
def create_user():
    """View to create a new user."""
    # TODO: define form fields here -- even though it doesn't make sense to
    #   define the form fields dynamically based on the table, we can still
    #   generate a list of fields to pass to the same html template.
    form_info = {
        'title': 'User',
        'fields': []
    }
    if flask.request.method == 'POST':
        title = flask.request.form['title']
        body = flask.request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            # Display error
            flask.flash(error)
        else:
            # Post is valid -- add to database
            db = profile.db.get_db()
            query = 'Insert INTO post (title, body, author_id) VALUES (?, ?, ?)'
            db.execute(query, (title, body, flask.g.user['id']))
            db.commit()
            return flask.redirect(flask.url_for('dashboard'))

    return flask.render_template('admin/create.html', form_info=form_info)


@bp.route('/create-post', methods=('GET', 'POST'))
@login_required
def create_post():
    """View to create a new post."""
    # Create form info
    form_info = {
        'title': 'Post',
        'fields': [
            {
                'field_name': 'title',
                'display_name': 'Post Title',
                'type': 'input',
            },
            {
                'field_name': 'body',
                'display_name': 'Post Body',
                'type': 'textarea',
            }
        ]
    }

    if flask.request.method == 'POST':
        title = flask.request.form['title']
        body = flask.request.form['body']
        error = None

        if not title:
            error = 'Title is required.'
            alert = 'danger'

        if error is not None:
            # Display error
            flask.flash(error, alert)
        else:
            # Post is valid -- add to database
            db = profile.db.get_db()
            query = 'Insert INTO post (title, body, author_id) VALUES (?, ?, ?)'
            db.execute(query, (title, body, flask.g.user['id']))
            db.commit()
            flask.flash('Post successfully added to database.', 'success')
            return flask.redirect(flask.url_for('admin.posts'))

    return flask.render_template('admin/create.html', form_info=form_info)


@bp.route('/create-publication', methods=('GET', 'POST'))
@login_required
def create_publication():
    """View to create a new publication."""
    # TODO: define form fields here -- even though it doesn't make sense to
    #   define the form fields dynamically based on the table, we can still
    #   generate a list of fields to pass to the same html template.
    form_info = {
        'title': 'Publication',
        'fields': []
    }
    if flask.request.method == 'POST':
        title = flask.request.form['title']
        body = flask.request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            # Display error
            flask.flash(error)
        else:
            # Post is valid -- add to database
            db = profile.db.get_db()
            query = 'Insert INTO post (title, body, author_id) VALUES (?, ?, ?)'
            db.execute(query, (title, body, flask.g.user['id']))
            db.commit()
            return flask.redirect(flask.url_for('dashboard'))

    return flask.render_template('admin/create.html', form_info=form_info)


def get_post(post_id, check_author=True):
    """Get post information from the database."""
    query = (
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?'
    )
    post = profile.db.get_db().execute(query, (post_id,)).fetchone()

    if post is None:
        flask.abort(404, f'Post id {post_id} does not exist')

    if check_author and post['author_id'] != flask.g.user['id']:
        flask.abort(403)

    return post


@bp.route('/<int:post_id>/update', methods=('GET', 'POST'))
@login_required
def update(post_id):
    """Update a post."""
    post = get_post(post_id)

    # Update post information if this is a post request
    if flask.request.method == 'POST':
        title = flask.request.form['title']
        body = flask.request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flask.flash(error)
        else:
            # Update post information in database
            db = profile.db.get_db()
            query = 'UPDATE post SET title = ?, body = ? WHERE id = ?'
            db.execute(query, (title, body, post_id))
            db.commit()
            return flask.redirect(flask.url_for('blog.index'))

    return flask.render_template('blog/update.html', post=post)


@bp.route('/<int:post_id>/delete', methods=('POST',))
@login_required
def delete(post_id):
    """Delete a post."""
    get_post(post_id)
    db = profile.db.get_db()
    query = 'DELETE from post WHERE id = ?'
    db.execute(query, (post_id, ))
    db.commit()
    return flask.redirect(flask.url_for('blog.index'))
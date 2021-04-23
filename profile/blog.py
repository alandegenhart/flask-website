import flask
import werkzeug.exceptions
import profile.admin
import profile.db


bp = flask.Blueprint('blog', __name__, url_prefix='/blog')


@bp.route('/')
def index():
    """Display posts"""
    db = profile.db.get_db()
    query = (
        'SELECT p.id, title, body, created, author_id, username' +
        ' FROM post p JOIN user u ON p.author_id = u.id' +
        ' ORDER BY created DESC'
    )
    posts = db.execute(query).fetchall()
    return flask.render_template('blog/index.html', posts=posts)


@bp.route('/create', methods=('GET', 'POST'))
@profile.admin.login_required
def create():
    """View to create a post."""
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
            return flask.redirect(flask.url_for('blog.index'))

    return flask.render_template('blog/create.html')


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
@profile.admin.login_required
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
@profile.admin.login_required
def delete(post_id):
    """Delete a post."""
    get_post(post_id)
    db = profile.db.get_db()
    query = 'DELETE from post WHERE id = ?'
    db.execute(query, (post_id, ))
    db.commit()
    return flask.redirect(flask.url_for('blog.index'))

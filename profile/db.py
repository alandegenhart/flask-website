import sqlite3
import click
import flask
import markupsafe


def get_db():
    if 'db' not in flask.g:
        flask.g.db = sqlite3.connect(
            flask.current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        flask.g.db.row_factory = sqlite3.Row

    return flask.g.db


def close_db(e=None):
    db = flask.g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    """Initialize the database."""
    db = get_db()
    with flask.current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


@click.command('init-db')  # Creates a command line command
@flask.cli.with_appcontext
def init_db_command():
    """Clear the existing db and create new tables."""
    init_db()
    click.echo('Initialized the database.')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


def get_posts(limit=10000):
    """Get (all) posts.
    Here we get the database reference, execute the query to get post info, and
    return.

    NOTE -- SQL doesn't appear to provide a way to set the limit to get all
    rows, so the max limit is set to 100k (there should never be this many
    posts)
    """
    # Query database for posts
    db = get_db()
    query = (
            'SELECT p.id, title, body, created, author_id, username' +
            ' FROM post p JOIN user ON author_id' +
            ' ORDER BY created DESC LIMIT ?'
    )
    posts = db.execute(query, (limit,)).fetchall()

    # Escape HTML for each post -- convert from a sqlite3 object to a dict b/c
    # row objects do not support assignment and we want to escape the HTML
    post_list = []
    for post in posts:
        post = dict(post)
        post['body'] = markupsafe.Markup(post['body'])
        post_list.append(post)

    return post_list

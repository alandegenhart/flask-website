import sqlite3
import click
import flask


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


def get_posts():
    """Get (all) posts.
    Here we get the database reference, execute the query to get post info, and
    return.

    Eventually this can be extended to limit the number of posts.
    """
    db = get_db()
    query = (
            'SELECT p.id, title, body, created, author_id, username' +
            ' FROM post p JOIN user ON author_id' +
            ' ORDER BY created DESC'
    )
    posts = db.execute(query).fetchall()
    return posts

import flask
import werkzeug.exceptions
import profile.auth
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

import flask
import os


def create_app(test_config=None):
    # Create and configure application
    app = flask.Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'site.sqline'),
    )

    # Load config
    if test_config is None:
        # Load instance config
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load test config if provided
        app.config.from_mapping(test_config)

    # Create instance folder
    os.makedirs(app.instance_path, exist_ok=True)

    # Create routes
    @app.route('/')
    def home():
        return flask.render_template('welcome.html')

    @app.route('/projects')
    def projects():
        return flask.render_template('projects.html')

    @app.route('/resume')
    def resume():
        return flask.render_template('resume.html')

    @app.route('/publications')
    def publications():
        return flask.render_template('publications.html')

    @app.route('/about')
    def about():
        return flask.render_template('about.html')

    # Initialize the application -- this includes generating the SQL
    import profile.db
    profile.db.init_app(app)

    import profile.auth
    app.register_blueprint(profile.auth.bp)

    return app

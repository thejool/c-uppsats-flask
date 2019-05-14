import os
from flask import Flask
from flask_bootstrap import Bootstrap


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flask.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    Bootstrap(app)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass


    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)
    app.add_url_rule('/', endpoint='index')

    # Global function for template files
    app.jinja_env.globals.update(get_user_name=auth.get_user_name)


    from . import file_handler
    app.register_blueprint(file_handler.bp)


    from . import perf_user
    app.register_blueprint(perf_user.bp)

    return app

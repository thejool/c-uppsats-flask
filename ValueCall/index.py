from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

bp = Blueprint('index', __name__)
@bp.route('/')
def index():
    if g.user != None:
        return render_template('users/index.html')
    else:
        return render_template('auth/login.html')

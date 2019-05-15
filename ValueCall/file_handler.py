import os
import datetime
import pandas as pd

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename

from pprint import pprint

from ValueCall.auth import (login_required, load_logged_in_user, get_user_name)
from ValueCall.db import get_db

bp = Blueprint('file_handler', __name__, url_prefix='/files')

ALLOWED_EXTENSIONS = set(['xlsx', 'csv'])
UPLOAD_FOLDER = os.path.abspath('.') + '/ValueCall/uploads/'


@bp.route('/')
@login_required
def files():
    db = get_db()
    uploads = db.execute(
        'SELECT * FROM uploads'
    )

    data = get_file_by_id(g.user['current_file'])
    filemeta = get_file_meta_by_id(g.user['current_file'])

    if data is None:
        return render_template('users/index.html', uploads=uploads)
    else:
        return render_template('users/index.html', uploads=uploads, tables=[data.head(100).to_html().replace('border="1"','border="0"')], filemeta=filemeta)


@bp.route('/change', methods=['POST'])
@login_required
def change():
    if request.method == 'POST':
        db = get_db()
        file_id = request.form.get('file')

        if g.user != None:
            db.execute(
                'UPDATE user SET current_file = (?) WHERE id = (?)', (file_id, str(g.user['id']))
            )
            db.commit()

    return redirect(url_for('file_handler.files'))


@bp.route('/remove/<int:file_id>')
@login_required
def remove(file_id):
    if file_id != None:
        db = get_db()
        filemeta = get_file_meta_by_id(file_id)

        os.remove(filemeta['filepath'])

        if g.user != None:
            db.execute(
                'UPDATE user SET current_file = (?) WHERE id = (?)', (0, str(g.user['id']))
            )

        db.execute(
            'DELETE FROM uploads WHERE id = (?)', (file_id,)
        )
        db.commit()
    else:
        flash("Välj fil att radera")

    return redirect(url_for('file_handler.files'))


@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':

        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            import xlrd
            import tempfile

            tempfile_path = tempfile.NamedTemporaryFile().name
            file.save(tempfile_path)

            if('xlsx' in file.filename):
                df = format_import(file, pd.read_excel(tempfile_path))

            elif('csv' in file.filename):
                df = format_import(file, pd.read_csv(tempfile_path))

            return redirect(url_for('file_handler.files'))

        else:
            flash('Wrong file format')

    return redirect(url_for('file_handler.files'))



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Get file information by the files path
def get_file_meta_by_path (filepath):
    db = get_db()
    error = None
    file = db.execute(
        'SELECT * FROM uploads WHERE filepath = (?)', (filepath,)
    ).fetchone()

    if file is None:
        error = 'Couldnt get file.'

    return file

# Get the file content by path
def get_file_by_path (filepath):
    file = get_file_meta_by_path(filepath)
    return pd.read_csv(file['filepath'])


# Get file meta by id
def get_file_meta_by_id (id):
    db = get_db()
    error = None
    file = db.execute(
        'SELECT * FROM uploads WHERE id = (?)', (id,)
    ).fetchone()

    if file is None:
        pprint('Couldnt get file.')

    return file

# Get file content by id
def get_file_by_id (id):
    error = None
    file_meta = get_file_meta_by_id(id)

    try:
        file = pd.read_csv(file_meta['filepath'], index_col=0)
    except:
        file = None

    return file


# Get all bookers by file id
def get_bookers (id):
    file_meta = get_file_meta_by_id(id)

    try:
        file = pd.read_csv(file_meta['filepath'], index_col=0)
    except:
        file = None

    return file.User_ID.unique()


def format_import (file, df):
    import numpy as np
    import urllib.request
    import json
    import seaborn as sns
    import matplotlib.pyplot as plt

    # Clear personal numbers for privacy reasons
    df.Personnr = df.Personnr.map(lambda x: (str(x)[0:10]))
    df.Personnr = pd.to_numeric(df.Personnr, errors='coerce')

    # All cities to lowercase
    df.Postadress_ort = df.Postadress_ort.str.lower()

    # Create attribute for age
    df["Alder"] = df.Personnr.map(lambda x: (2019-float(str(x)[0:4])))

    # Drop all missing values
    df = df.dropna(axis='index')

    # Drop all wrongly formatted birth dates
    df = df.drop(df.loc[df['Personnr'] < 19000101].index)

    # Exclude users like the dialer
    exclude_users = [99, 100, 102, 108, 168]

    for user in exclude_users:
        df = df.drop(df.loc[df['Anvandare_ID'] == user].index)

    # Format yes/no to easy calculate hit rate
    df["Ja"]  = df.Utfall.map(lambda x: 1 if x == "Bokning" else 0)
    df["Nej"] = df.Utfall.map(lambda x: 1 if x == "Nej" else 0)

    # Rename columns
    df.rename(columns={'Anvandare_ID':'User_ID', 'Postadress_ort':'Ort', 'Postadress_postnr':'Postnr'}, inplace=True)

    # Reset df index
    df = df.reset_index(drop=True)

    # Current timestamp
    time = datetime.datetime.now()
    timestamp_csv = str(time.strftime("%Y-%m-%d_%H%-M%-S")) + ".csv"

    # Save the file to the defined location
    filepath = os.path.join(UPLOAD_FOLDER, timestamp_csv)
    df.to_csv(filepath)

    db = get_db()

    db.execute(
        'INSERT INTO uploads (filepath, filename, upload_date, uploaded_by) VALUES (?, ?, ?, ?)',
        (filepath, timestamp_csv, datetime.datetime.now(), g.user['id'])
    )

    file_meta = get_file_meta_by_path(filepath)

    if g.user != None:
        db.execute(
            'UPDATE user SET current_file = (?) WHERE id = (?)', (file_meta['id'], str(g.user['id']))
        )

    db.commit()


    return df

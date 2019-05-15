import os
import datetime

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename

from pprint import pprint

from ValueCall.auth import (login_required, load_logged_in_user, get_user_name)
from ValueCall.file_handler import (get_file_by_id, get_file_meta_by_id, get_bookers)
from ValueCall.db import get_db

bp = Blueprint('perf_user', __name__, url_prefix='/performance')


@bp.route('/user', methods=['GET', 'POST'])
@login_required
def user():
    if g.user['current_file'] == 0:
        flash("Du måste välja en fil först")
        return redirect(url_for('file_handler.files'))

    else:
        filemeta = get_file_meta_by_id(g.user['current_file'])
        bookers = get_bookers(g.user['current_file'])
        users = []

        if request.method == 'POST':
            data = []
            user_1 = int(request.form.get('user_1'))
            user_2 = int(request.form.get('user_2'))

            if user_1 != 0:
                users.append(user_1)

                user_1 = get_age_perf_by_user(user_1)
                table = [user_1['table'].head(100).to_html().replace('border="1"','border="0"')]

                histogram = user_1['histogram']
                diagram = user_1['diagram']

                data.append(dict([('tables', table), ('histogram', histogram), ('diagram', diagram)]))

            if user_2 != 0:
                users.append(user_2)

                user_2 = get_age_perf_by_user(user_2)
                table = [user_2['table'].head(100).to_html().replace('border="1"','border="0"')]
                histogram = user_2['histogram']
                diagram = user_2['diagram']

                data.append(dict([('tables', table), ('histogram', histogram), ('diagram', diagram)]))

            
            if len(data) == 0:
                return render_template('performance/user.html', 
                    filemeta=filemeta,
                    users=users,
                    bookers=bookers)
            else:
                return render_template('performance/user.html', 
                    data=data,
                    filemeta=filemeta,
                    users=users,
                    bookers=bookers)
        else:
            return render_template('performance/user.html', 
                filemeta=filemeta,
                users=users,
                bookers=bookers)


def get_age_perf_by_user(user):
    import pandas as pd
    import matplotlib.pyplot as plt

    df = get_file_by_id(g.user['current_file'])

    # Get only data for the specific user
    user_perf = df.loc[df['User_ID'] == user]

    # Only calls that are hits or none hits
    user_perf = pd.concat([user_perf.loc[user_perf['Utfall'] == 'Bokning'], user_perf[user_perf['Utfall'] == 'Nej']])

    # Aggregate data on age
    aggregation_functions = {'User_ID': 'first', 'Alder': 'first', 'Ja': 'sum', 'Nej': 'sum'}

    # Group data by age
    user_perf = user_perf.groupby(user_perf['Alder']).aggregate(aggregation_functions)

    # Calculate hit rate per age
    user_perf['Hit_Rate'] = user_perf['Ja'] / (user_perf['Nej'] + user_perf['Ja'])

    # Reset user_perf index
    user_perf = user_perf.reset_index(drop=True)

    # Plot histogram
    fig_histogram, ax = plt.subplots()
    
    ax.bar(list(user_perf['Hit_Rate'].keys()), list(user_perf['Hit_Rate']))
    fig_histogram = fig_to_base64(fig_histogram).decode('utf8')

    # Plot diagram
    fig_diagram, ax = plt.subplots()
    ax.plot(user_perf['Hit_Rate'])
    fig_diagram = fig_to_base64(fig_diagram).decode('utf8')


    # Sort by hit rate
    #user_perf = user_perf.sort_values(by=['Hit_Rate'], ascending=False)
    
    result = dict([('table', user_perf), ('histogram', fig_histogram), ('diagram', fig_diagram)])
    return result



def fig_to_base64(fig):
    import io
    import base64

    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)

    return base64.b64encode(img.read())


import os
import datetime
import pandas as pd
import matplotlib.pyplot as plt

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from pprint import pprint

from ValueCall.auth import (login_required, load_logged_in_user)
from ValueCall.file_handler import (get_file_by_id, get_file_meta_by_id)

bp = Blueprint('perf_global', __name__, url_prefix='/performance')


@bp.route('/')
@login_required
def performance():
    filemeta = get_file_meta_by_id(g.user['current_file'])

    age_data = get_age_perf()
    age = age_data['table'].head(100).to_html().replace('border="1"','border="0"')
    
    location_data = get_location_perf()
    location = location_data['table'].head(100).to_html().replace('border="1"','border="0"')
    
    histogram = age_data['histogram']

    data = [dict([('tables', [age, location]), ('histogram', histogram)])]
        
    return render_template('performance/performance.html', 
        filemeta=filemeta,
        data=data)


def get_age_perf():
    df_age = get_file_by_id(g.user['current_file'])

    # Only calls that are hits or none hits
    df_age = pd.concat([df_age.loc[df_age['Utfall'] == 'Bokning'], df_age[df_age['Utfall'] == 'Nej']])

    # Aggregate data on location
    aggregation_functions = {'Alder': 'first', 'Ja': 'sum', 'Nej': 'sum'}

    # Group data by location
    df_age = df_age.groupby(df_age['Alder']).aggregate(aggregation_functions)

    # Calculate hit rate per age
    df_age['Hit_Rate'] = df_age['Ja'] / (df_age['Nej'] + df_age['Ja'])

    # Plot histogram
    fig_histogram, ax = plt.subplots()
    ax.bar(list(df_age['Hit_Rate'].keys()), list(df_age['Hit_Rate']))
    fig_histogram = fig_to_base64(fig_histogram).decode('utf8')

    # Sort by hit rate
    df_age = df_age.sort_values(by=['Hit_Rate'], ascending=False)
    result = dict([('table', df_age), ('histogram', fig_histogram)])
    return result


def get_location_perf():
    df_location = get_file_by_id(g.user['current_file'])

    # Only calls that are hits or none hits
    df_location = pd.concat([df_location.loc[df_location['Utfall'] == 'Bokning'], df_location[df_location['Utfall'] == 'Nej']])

    # Aggregate data on location
    aggregation_functions = {'Ort': 'first', 'Ja': 'sum', 'Nej': 'sum'}

    # Group data by location
    df_location = df_location.groupby(df_location['Ort']).aggregate(aggregation_functions)

    # Calculate hit rate per age
    df_location['Hit_Rate'] = df_location['Ja'] / (df_location['Nej'] + df_location['Ja'])

    # Sort by hit rate
    df_location = df_location.sort_values(by=['Hit_Rate'], ascending=False)

    # Sort by hit rate
    df_age = df_location.sort_values(by=['Hit_Rate'], ascending=False)
    result = dict([('table', df_location)])
    return result




def fig_to_base64(fig):
    import io
    import base64

    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)

    return base64.b64encode(img.read())


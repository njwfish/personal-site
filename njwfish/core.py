from flask import Blueprint, render_template, abort, url_for
from jinja2 import TemplateNotFound

import os

core = Blueprint('core', __name__,
                 template_folder='templates')


@core.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(core.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


@core.route('/')
@core.route('/index')
def index():
    try:
        return render_template('about.html')
    except TemplateNotFound:
        abort(404)


@core.route('/contact')
def contact():
    try:
        return render_template('contact.html')
    except TemplateNotFound:
        abort(404)


@core.route('/projects')
def projects():
    try:
        return render_template('projects.html')
    except TemplateNotFound:
        abort(404)

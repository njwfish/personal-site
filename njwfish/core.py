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
        projects = []
        projects_dir = os.path.join(*[os.path.dirname(__file__), 'static', 'projects'])

        for folder in os.walk(projects_dir):
            if folder[0].split('/')[-1] == "projects":
                continue
            files = folder[2]
            assert(len(files) == 2)
            dir_info = os.path.join(*folder[0].split('/')[-3:]) + '/'
            if 'png' in files[0] or 'jpg' in files[0]:
                projects.append((dir_info + files[0], dir_info + files[1]))
            else:
                projects.append((dir_info + files[1], dir_info + files[0]))

        return render_template('projects.html', projects=projects)
    except TemplateNotFound:
        abort(404)

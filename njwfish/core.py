from flask import Blueprint, render_template, abort, url_for, send_from_directory
import markdown
import codecs
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
@core.route('/about')
def index():
    try:
        post = md_to_html('static/about.md')
        return render_template('about.html', post=post)
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
            if folder[0].split('/')[-1] == "projects" or folder[0].split('/')[-1] == "static":
                continue
            files = folder[2]
            dir_info = os.path.join(*folder[0].split('/')[-3:]) + '/'
            projects.append((dir_info + 'thumbnail.png', url_for('.project', project_name=folder[0].split('/')[-1]),
                             os.path.getmtime(dir_info)))
        projects = sorted(projects, key=lambda x: x[2], reverse=True)
        return render_template('projects.html', projects=projects)
    except TemplateNotFound:
        abort(404)

def md_to_html(md):
    input_file = codecs.open(md, mode="r", encoding="utf-8")
    text = input_file.read()
    return markdown.markdown(text)

@core.route('/project/<project_name>')
def project(project_name):
    try:
        folder = [os.path.dirname(__file__), 'static', 'projects', project_name]
        dir_info = os.path.join(*folder) + '/'

        image = dir_info + 'thumbnail.png'
        url = url_for('.project', project_name=project_name)
        post = md_to_html(dir_info + 'post.md')
        urls = []
        for url_ in open(dir_info + 'urls.txt', 'r'):
            url_ = url_ if url_[0] != '/' else url_for('static', filename=url_[1:])
            url_name = url_.split('/')[2].split('.')[0] if url_[0] != '/' else url_.split('/')[-1].split('.')[0]
            urls.append((url_, url_name))
        project_name = project_name.replace('-', ' ')
        return render_template('project.html', project_name=project_name, image=image, url=url, urls=urls, post=post)
    except TemplateNotFound:
        abort(404)

from flask import Blueprint, render_template, abort, url_for, send_from_directory
import markdown
import codecs
from jinja2 import TemplateNotFound
import time
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


@core.route('/resume')
def resume():
    try:
        return send_from_directory('static', 'resume.pdf')
    except TemplateNotFound:
        abort(404)

@core.route('/papers')
def papers():
    try:
        return render_template('papers.html')
    except TemplateNotFound:
        abort(404)


@core.route('/words')
def posts():
    try:
        posts = []
        posts_dir = os.path.join(*[os.path.dirname(__file__), 'static', 'posts'])

        for folder in os.walk(posts_dir):
            if folder[0].split('/')[-1] == "posts" or folder[0].split('/')[-1] == "static":
                continue
            files = folder[2]

            dir_info = os.path.join(*folder[0].split('/')[-3:]) + '/'

            title = open(dir_info + 'title', "r").read()
            blurb = open(dir_info + 'blurb', "r").read()
            posts.append((url_for('.post', post=folder[0].split('/')[-1]),
                          title, blurb,
                          time.strftime('%m/%d/%Y', time.gmtime(os.path.getmtime(dir_info)))))
        posts = sorted(posts, key=lambda x: x[2], reverse=True)
        return render_template('posts.html', posts=posts)
    except TemplateNotFound:
        abort(404)

def md_to_html(md):
    input_file = codecs.open(md, mode="r", encoding="utf-8")
    text = input_file.read()
    return markdown.markdown(text)

@core.route('/words/<post>')
def post(post):
    try:
        folder = [os.path.dirname(__file__), 'static', 'posts', post]
        dir_info = os.path.join(*folder) + '/'

        post_text = md_to_html(dir_info + 'main.md')
        return render_template('post.html', post=post_text)
    except TemplateNotFound:
        abort(404)

import base64
import binascii
import flask
import functools
import hashlib
from sqlalchemy import exc
from sqlalchemy.orm import exc as orm_exc
import subprocess

from pwntalk import models
from pwntalk.app import app, get_flag


def require_login(func):
  """Send to homepage if not logged in."""
  @functools.wraps(func)
  def _login_wrapper(*args, **kwargs):
    if not _check_login():
      return flask.redirect(flask.url_for('home'))
    return func(*args, **kwargs)
  return _login_wrapper


@app.route('/')
def home():
  _check_login()
  return _render_posts_page(models.Post.query)


@app.route('/login', methods=['POST'])
def login():
  try:
    user = models.User.query.filter(
        models.User.username == flask.request.form['username'],
        models.User.password == flask.request.form['password']
        ).one()
    flask.session['user'] = user.uid
  except orm_exc.NoResultFound:
    flask.flash('Invalid username and/or password.', 'warning')
  return flask.redirect(flask.url_for('home'))


@app.route('/logout', methods=['GET', 'POST'])
def logout():
  del flask.session['user']
  flask.flash('You are now logged out.', 'success')
  return flask.redirect(flask.url_for('home'))


@app.route('/register', methods=['POST'])
def register():
  try:
    user = models.User.register(
        flask.request.form['username'],
        flask.request.form['email'],
        flask.request.form['password'])
    flask.session['user'] = user.uid
    flask.flash('Registration successful.', 'success')
  except exc.IntegrityError:
    flask.flash('Duplicate username or email.', 'danger')
  return flask.redirect(flask.url_for('home'))


@app.route('/profile', methods=['GET', 'POST'])
@require_login
def profile():
  _validate_csrf()
  flag = None
  if flask.request.method == 'POST':
    user = models.User.query.get(flask.request.form.get('uid'))
    if not user:
      abort(404)
    user.tagline = flask.request.form.get('tagline')
    models.commit()
    flask.flash('Profile updated.', 'success')
    # Check for flag
    if user.username == 'root' and flask.g.user.username in user.tagline:
      flag = get_flag('user_profile_edited')
  return _render_page('profile.html', flag=flag, user=flask.g.user)


@app.route('/post', methods=['POST'])
@require_login
def post():
  _validate_csrf()
  text = flask.request.form['text']
  if not text:
    flask.flash('Text is required.', 'warning')
  elif len(text) > 200:
    flask.flash('Text cannot be more than 200 characters.', 'warning')
  else:
    models.Post.post(flask.g.user, text)
  return flask.redirect(flask.request.form['redir'])


@app.route('/u/<username>')
def user_page(username):
  _check_login()
  # SQLi
  try:
    query = 'SELECT * FROM user WHERE (username=\'%s\')' % username
    user = models.User.query.from_statement(query).one()
  except (exc.OperationalError, orm_exc.NoResultFound):
    user = None
  if not user:
    flask.flash('No such user!', 'warning')
    return _render_page('error.html')
  posts = user.posts
  return _render_posts_page(posts, user_profile=user)


@app.route('/status', methods=['GET', 'POST'])
@require_login
def status():
  def _make_admin_cookie(admin_value='False'):
    raw = '%s|%s' % (flask.g.user.username, admin_value)
    return base64.b64encode('%s|%s' % (raw, hashlib.md5(raw).hexdigest()))

  def _validate_admin_cookie(cookie):
    parts = base64.b64decode(cookie).split('|')
    admin_value = parts[1]
    if cookie != _make_admin_cookie(admin_value):
      return False
    return admin_value == 'True'

  admin_cookie = flask.request.cookies.get('admin_status')
  if not admin_cookie or not _validate_admin_cookie(admin_cookie):
    resp = flask.make_response('Access Denied.', 403)
    resp.set_cookie('admin_status', _make_admin_cookie())
    return resp
  page = flask.request.values.get('page', 'uptime')
  # Sanitize this so users can't read everything
  try:
    hexpage = binascii.hexlify(page)
    output = subprocess.check_output(['tools/cmdwrapper', hexpage],
        shell=False)
  except Exception as ex:
    flask.flash('Invalid command: ' + str(ex), 'danger')
    return _render_page('error.html')
  return _render_page(
      'status.html', flag=get_flag('admin_console'), output=output)


@app.route('/robots.txt')
def robots_txt():
  return open(flask.url_for('static', filename='robots.txt')).read()


def _render_posts_page(posts, **kwargs):
  flag = None
  if posts:
    posts = posts.order_by(models.Post.posted.desc()).limit(20)
    # Check for win
    if 'user' in flask.g:
      username = flask.g.user.username
      for post in posts:
        if (post.author.username == 'HaplessTechnoweenie' and 
            username in post.text):
          flag = get_flag('dom_based_xss')
    # TODO: pagination?
  return _render_page(
      'posts.html', posts=posts, flag=flag, **kwargs)


def _render_page(page, **kwargs):
  return flask.render_template(page, csrftoken=_csrf_token(), **kwargs)


def _check_login():
  if 'user' in flask.session:
    if not 'user' in flask.g:
      flask.g.user = models.User.query.get(int(flask.session['user']))
    return flask.g.user


def _csrf_token():
  _check_login()
  try:
    username = flask.g.user.username
  except AttributeError:
    return ''
  md5sum = hashlib.md5(username).hexdigest()
  return base64.b64encode('%s:%s' % (username, md5sum))


def _validate_csrf():
  csrftoken = _csrf_token()
  if flask.request.method != 'GET' and (not csrftoken or
      flask.request.form['csrftoken'] != csrftoken):
    print 'csrf check failed, got %s, expected %s' % (
        flask.request.form['csrftoken'], csrftoken)
    flask.abort(403)
  return csrftoken

# Copyright 2014 David Tomaschik <david@systemoverlord.com>
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import functools
import hashlib
import flask
import json
import os.path
import re
from pwncart import models
from pwncart.app import app, get_flag

# Shortcuts
request, session = flask.request, flask.session


def require_login(func):
  """Send to homepage if not logged in."""
  @functools.wraps(func)
  def _login_wrapper(*args, **kwargs):
    if 'user' not in session:
      return flask.redirect(flask.url_for('home'))
    return func(*args, **kwargs)
  return _login_wrapper


def require_admin(func):
  """Require admin on post."""
  @functools.wraps(func)
  def _admin_wrapper():
    admin_cookie = request.cookies.get('admin')
    expected = app.config['ADMIN_TOKEN']
    if admin_cookie != expected:
      app.logger.warning('Admin token failure, expected %s, got %s' % 
          (expected, admin_cookie))
      flask.abort(403)
    else:
      return func()
  return _admin_wrapper


@app.route('/catalog')
@require_login
def catalog():
  items = models.Item.query.all()
  return flask.render_template('catalog.html', items=items)


@app.route('/catalog/<int:item>')
@require_login
def catalog_item(item):
  item = models.Item.query.get_or_404(item)
  comments = item.comments.filter(models.Comment.approved == True)
  return flask.render_template('catalog_item.html', item=item, comments=comments)


@app.route('/cart', methods=['GET', 'POST'])
@require_login
def shopping_cart():
  try:
    cart = json.loads(request.cookies.get('cart', '{}'))
  except ValueError:
    flask.flash('Invalid cart.', 'warning')
    cart = {}
  total = _total_price(cart)
  if request.method == 'GET':
    return flask.render_template('cart.html', cart=cart, total=total)
  # Replace cart with updated version
  if 'add' in request.form:
    item = request.form['add']
    cart[item] = models.Item.query.get_or_404(item).to_cart()
  elif 'del' in request.form:
    item = request.form['del']
    try:
      del cart[item]
    except KeyError:
      pass
  resp = flask.make_response(flask.render_template('cart.html', cart=cart,
    total=_total_price(cart)))
  resp.set_cookie('cart', json.dumps(cart))
  return resp


@app.route('/checkout', methods=['POST'])
@require_login
def checkout():
  cart = json.loads(request.cookies.get('cart', '{}'))
  if not len(cart):
    return flask.redirect(flask.url_for('shopping_cart'))
  total = _total_price(cart)
  if total > 0:
    flask.flash('Sorry, our payment processor is down, can only check '
                'out free items.', 'warning') 
    return flask.redirect(flask.url_for('shopping_cart'))
  flag = get_flag('free_cart') if u'1337' in cart else None
  order = models.Order()
  order.username = session['user']
  order.order_data = request.cookies.get('cart')
  order.total = total
  models.db.session.add(order)
  models.db.session.commit()
  resp = flask.make_response(flask.render_template('checkout.html',
    flag=flag))
  resp.set_cookie('cart', '{}')
  return resp


def _total_price(cart):
  return sum(int(i['price']) for i in cart.itervalues())/100


@app.route('/')
def home():
  """Login & registration form."""
  if 'user' in session:
    return flask.redirect(flask.url_for('catalog'))
  return flask.render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
  """Login."""
  username = request.form.get('username')
  password = request.form.get('password')
  if not username:
    flask.flash('Username is required.', 'warning')
  elif password is None:
    flask.flash('Password is required.', 'warning')
  else:
    user = models.User.login_user(username, password)
    if user:
      session['user'] = user.username
      return flask.redirect(flask.url_for('catalog'))
    flask.flash('Invalid username/password.', 'danger')
  return flask.redirect(flask.url_for('home'))


@app.route('/logout', methods=['GET', 'POST'])
def logout():
  """Logout."""
  if 'user' in session:
    del session['user']
  return flask.redirect(flask.url_for('home'))


@app.route('/register', methods=['POST'])
def register():
  """Registration form handler."""
  def fail_validate(msg):
    flask.flash(msg, 'danger')
    return flask.redirect(flask.url_for('home'))

  username = request.form.get('username', '')
  if not re.match(r'[A-Za-z0-9_]+$', username):
    return fail_validate('Invalid username.')
  if models.User.query.get(username):
    return fail_validate('User exists.')

  user = models.User()
  user.username = username
  user.password = request.form.get('password')
  user.email = request.form.get('email', '')
  if models.User.query.filter(models.User.email == user.email).count():
    return fail_validate('User exists with that email address.')
  models.db.session.add(user)
  models.db.session.commit()
  session['user'] = user.username
  return flask.redirect(flask.url_for('catalog'))


@app.route('/profile')
@require_login
def profile():
  user = models.User.query.get(session['user'])
  flag = get_flag('account_credit') if user.credit >= 700 else None
  return flask.render_template('profile.html', user=user, flag=flag)


@app.route('/review_comments')
@require_admin
def review_comments():
  comment = models.Comment.query.filter(models.Comment.reviewed ==
      False).first()
  if comment:
    comment.mark_reviewed()
  return flask.render_template('comments.html', comment=comment)


@app.route('/comment/<int:item>', methods=['POST'])
@require_login
def comment(item):
  c = models.Comment()
  c.itemno = item
  c.username = session['user']
  c.approved = False
  c.comment = request.values.get('comment')
  models.db.session.add(c)
  models.db.session.commit()
  flask.flash('Comment added to moderation queue for admin review.', 'success')
  return flask.redirect(flask.url_for('catalog_item', item=item))


@app.route('/apply_credit', methods=['GET', 'POST'])
def apply_credit():
  if request.method == 'POST':
    _apply_credit_post()
  return flask.render_template('apply_credit.html')


@require_admin
def _apply_credit_post():
  username = request.values.get('username')
  user = models.User.query.get_or_404(username)
  user.credit += int(request.values.get('amount', 0))
  models.db.session.commit()
  flask.flash('Credit applied.', 'success')


@app.route('/robots.txt')
def robots():
  return app.send_static_file('robots.txt')


@app.route('/download')
def download():
  # TODO: deal with content types
  def join_paths(*args):
    trimmed = [x[1:] if x[0] == '/' else x for x in args[1:]]
    return os.path.realpath(os.path.join(args[0], *trimmed))
  path = request.values.get('file')
  if not path:
    flask.abort(400)
  path = join_paths(app.config['DOWNLOAD_DIR'], path)
  if path.startswith(app.config['DOWNLOAD_DIR']):
    if not os.path.isfile(path):
      app.logger.warning('Download not in DIR requested: %s' % path)
      flask.abort(403)
    return flask.send_file(path)
  # Now fake chroot
  path = join_paths(app.config['SANDBOX_DIR'], path)
  # Double check
  if not path.startswith(app.config['SANDBOX_DIR']):
    app.logger.warning('Download not in sandbox requested: %s' % path)
    flask.abort(500)
  if not os.path.isfile(path):
    app.logger.warning('Download not found: %s' % path)
    flask.abort(404)
  return flask.send_file(path)

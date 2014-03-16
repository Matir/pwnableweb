import base64
import datetime
import hashlib
import flask
import os
import random

from flask.ext import sqlalchemy
from pwntalk.app import app, get_flag

db = sqlalchemy.SQLAlchemy(app)
commit = db.session.commit


class User(db.Model):
  uid = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(100), unique=True)
  email = db.Column(db.String(100), unique=True)
  password = db.Column(db.String(40))
  tagline = db.Column(db.String(200))
  posts = db.relationship('Post',
      backref=db.backref('author', lazy='joined'),
      lazy='dynamic')

  @classmethod
  def register(cls, username, email, password):
    user = cls()
    user.username = username
    user.email = email
    user.password = password
    user.tagline = 'Just a n00b.'
    db.session.add(user)
    db.session.commit()
    return user


class Post(db.Model):
  pid = db.Column(db.Integer, primary_key=True)
  author_id = db.Column(db.Integer, db.ForeignKey('user.uid'))
  posted = db.Column(db.DateTime, default=datetime.datetime.utcnow)
  text = db.Column(db.String(200))

  @classmethod
  def post(cls, author, text):
    p = cls()
    p.author = author
    p.text = text
    db.session.add(p)
    db.session.commit()
    return p

  def date(self):
    return self.posted.strftime('%Y-%m-%d %H:%M')


def create_data():
  # Setup users
  users = []
  user = User()
  user.username = 'HaplessTechnoweenie'
  user.password = hashlib.sha1('HaplessTechnoweenie1').hexdigest()
  user.tagline = 'Type cookie, you idiot!'
  user.email = 'jillette@gibson.biz'
  db.session.add(user)
  users.append(user)

  user = User()
  user.username = 'root'
  user.password = base64.b64encode(os.urandom(12))
  user.tagline = 'UID 0 FTW!'
  user.email = 'root@localhost'
  db.session.add(user)
  users.append(user)

  user = User()
  user.username = 'larry'
  user.password = get_flag('larry_pass')
  user.tagline = 'Living the island life!'
  user.email = 'l@le.com'
  db.session.add(user)
  users.append(user)

  # Create some more test users
  for name in ['edward', 'michael', 'daniel', 'rob', 'ron']:
    user = User()
    user.username = name
    user.email = name + '@example.org'
    user.tagline = 'Just a PwnTalk user.'
    user.password = base64.b64encode(os.urandom(12))
    db.session.add(user)
    users.append(user)

  # Create some test messages
  msgs = [
      "Check out this awesome blog: https://systemoverlord.com",
      "Are we fashionably late?",
      "There is no right and wrong. There's only fun and boring.",
      "I don't play well with others.",
      "Never fear, I is here.",
      "Quis custodiet ipsos custodes?",
      "\"They who can give up essential liberty to obtain a little "
        "temporary safety deserve neither liberty nor safety.\" --Ben Franklin",
      "\"Those who deny freedom to others deserve it not for themselves.\" "
        "--Abe Lincoln",
      "\"When the people fear the government there is tyranny, when the "
        "government fears the people there is liberty.\" --Jefferson",
      "OWASP Top 10: "
        "https://www.owasp.org/index.php/Top_10_2013-Table_of_Contents",
      ]

  for user in users:
    random.shuffle(msgs)
    for msg in msgs[:random.randint(3,5)]:
      # TODO: fudge timestamps
      post = Post()
      post.author = user
      post.text = msg
      db.session.add(post)

  print "Committing..."
  db.session.commit()

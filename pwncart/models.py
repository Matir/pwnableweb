import hashlib
import flask
from flask.ext import sqlalchemy
from pwncart.app import app

db = sqlalchemy.SQLAlchemy(app)


class User(db.Model):
  username = db.Column(db.String(100), primary_key=True)
  email = db.Column(db.String(100), unique=True)
  pwhash = db.Column(db.String(100))
  credit = db.Column(db.Numeric(8, 2), default=0)
  orders = db.relationship('Order', backref='user', lazy='dynamic')
  comments = db.relationship('Comment', backref='user', lazy='dynamic')

  def __str__(self):
    return self.username

  def __repr__(self):
    return '<User %r>' % self.username

  @property
  def password(self):
    return self.pwhash

  @password.setter
  def password(self, pw):
    self.pwhash = self.hash_password(pw)

  @classmethod
  def login_user(cls, username, password):
    # Validate login, then get by username
    res = db.engine.execute("select username from " + cls.__tablename__ + 
        " where username='" + username + "' and pwhash='" +
        cls.hash_password(password) + "'")
    row = res.fetchone()
    if not row:
      return
    return cls.query.get(row[0])

  @staticmethod
  def hash_password(pw):
    return hashlib.sha1(pw).hexdigest()


class Item(db.Model):
  catno = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100))
  description = db.Column(db.String(200))
  attachment = db.Column(db.String(100))
  price = db.Column(db.Numeric(8, 2))
  img_name = db.Column(db.String(120))
  comments = db.relationship('Comment', backref='item', lazy='dynamic')

  def __str__(self):
    return self.name

  def __repr__(self):
    return '<Item %d>' % self.catno

  def to_cart(self):
    return {
        'catno': self.catno,
        'name': self.name,
        'price': int(self.price * 100),
        }

  def imgurl(self):
    return flask.url_for('static', filename='img/products/'+self.img_name)


class Order(db.Model):
  orderno = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(100), db.ForeignKey('user.username'))
  # Just store the order as a blob
  order_data = db.Column(db.LargeBinary)
  total = db.Column(db.Numeric(8, 2))


class Comment(db.Model):
  cid = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(100), db.ForeignKey('user.username'))
  itemno = db.Column(db.Integer, db.ForeignKey('item.catno'))
  comment = db.Column(db.Text)
  reviewed = db.Column(db.Boolean, default=False)
  approved = db.Column(db.Boolean)

  def mark_reviewed(self):
    self.reviewed = True
    db.session.commit()


def create_data():
  user = User()
  user.username = 'lord_nikon'
  user.password = 'ph0t0mem0ry!'
  user.email = 'nikon@photographic-memory.info'
  db.session.add(user)
  user = User()
  user.username = 'CrashOverride'
  user.password = 'messwiththebest,dieliketherest'
  user.email = 'crash@gibson.biz'
  db.session.add(user)
  item = Item()
  item.catno = 1337
  item.name = 'Gibson Laptop'
  item.description = 'Your very own Gibson, now in a laptop!'
  item.price = 915.95
  item.img_name = 'gibson.jpg'
  item.attachment = 'Brochure.pdf'
  db.session.add(item)
  item = Item()
  item.catno = 1057
  item.name = 'Lost Parallax Designs'
  item.description = 'Blueprints to some of Parallax Finest Products'
  item.price = 864.00
  item.img_name = 'lost.jpg'
  db.session.add(item)

  db.session.commit()

import sys

from pwntalk.app import app
from pwntalk import models
# Needed to define views
from pwntalk import views


if __name__ == '__main__':
  if 'createdb' in sys.argv:
    models.db.create_all()
    models.create_data()
  else:
    app.run(debug=True, port=app.config['PORT'])

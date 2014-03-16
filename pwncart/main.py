import sys

from pwncart.app import app
from pwncart import models
# Needed to define views
from pwncart import views


if __name__ == '__main__':
  if 'createdb' in sys.argv:
    models.db.create_all()
    models.create_data()
  else:
    app.run(debug=True, port=app.config['PORT'])

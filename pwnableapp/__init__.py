import logging
import flask
import sys

class Flask(flask.Flask):

  def __init__(self, *args, **kwargs):
    super(Flask, self).__init__(*args, **kwargs)
    # Set error handlers
    self.register_error_handler(500, self.internal_error_handler)
    for error in (400, 403, 404):
      self.register_error_handler(error, self.make_error_handler(error))

  def init_logging(self):
    """Must be called after config setup."""
    if not self.debug:
      handler = logging.FileHandler(
          self.config.get('LOG_FILE', '/tmp/flask.log'))
      handler.setFormatter(logging.Formatter(
          '%(asctime)s %(levelname)8s [%(filename)s:%(lineno)d] %(message)s'))
      handler.setLevel(logging.INFO)
      self.logger.addHandler(handler)

  def internal_error_handler(self, message=None):
    return flask.make_response(flask.render_template(
      'error.html',
      message=message,
      code=500,
      exc=sys.exc_info()[1]), 500)

  def make_error_handler(self, code):
    def _error_handler(message=None):
      return flask.make_response(flask.render_template(
        'error.html', message=message, code=code))
    return _error_handler

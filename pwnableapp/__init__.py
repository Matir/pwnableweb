import logging
import flask

class Flask(flask.Flask):

  def init_logging(self):
    """Must be called after config setup."""
    if not self.debug:
      handler = logging.FileHandler(
          self.config.get('LOG_FILE', '/tmp/flask.log'))
      handler.setFormatter(
          '%(asctime)s %(levelname)8s [%(filename)s:%(lineno)d] %(message)s')
      handler.setLevel(logging.INFO)
      self.logger.addHandler(handler)

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

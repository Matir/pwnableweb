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

import time
from flask import url_for
from selenium.common.exceptions import NoSuchElementException

from pwnableapp import client
from pwncart.app import app
import pwncart.views


class PwnCartClient(client.VulnerableClient):

  def __init__(self, **kwargs):
    if ('chromedriver_path' not in kwargs and 
        'chromedriver_path' in app.config):
      kwargs['chromedriver_path'] = app.config['chromedriver_path']
    super(PwnCartClient, self).__init__('PwnCartClient', **kwargs)
  
  def run(self):
    with app.app_context():
      url = url_for('review_comments', _external=True)
    print 'Loading %s' % url
    self.browser.get(url)
    if 'Forbidden' in self.browser.title:
      self.browser.add_cookie({'name': 'admin',
        'value': app.config['ADMIN_TOKEN']})
      self.browser.get(url)
    try:
      if self.browser.find_element_by_id('pending-comment'):
        print 'Found pending comment.'
        # Wait for attacks
        time.sleep(5)
        return True
    except NoSuchElementException:
      pass


if __name__ == '__main__':
  client = PwnCartClient(chromedriver_path='/opt/chromedriver')
  client.start()

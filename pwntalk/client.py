import hashlib
import time
from flask import url_for
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

from pwnableapp import client
from pwntalk.app import app
import pwntalk.views


class PwnTalkClient(client.VulnerableClient):

  def __init__(self, **kwargs):
    if ('chromedriver_path' not in kwargs and 
        'chromedriver_path' in app.config):
      kwargs['chromedriver_path'] = app.config['chromedriver_path']
    super(PwnTalkClient, self).__init__(**kwargs)
    # Setup
    self.visited = set()
  
  def run(self):
    with app.app_context():
      url = url_for('direct_messages', _external=True)
    print 'Loading %s' % url
    self.browser.get('about:blank')
    self.browser.get(url)
    try:
      self.browser.find_element_by_id('new-post-form')
    except NoSuchElementException:
      self._perform_login('HaplessTechnoweenie',
          hashlib.sha1('HaplessTechnoweenie1').hexdigest())
      self.browser.get(url)
    self._visit_links()

  def _perform_login(self, username, password):
    """Login to site."""
    modal_link = self.browser.find_element_by_id('register-link')
    self.chain.move_to_element(modal_link).click(modal_link).perform()
    user_field = self.browser.find_element_by_id('login-username')
    pass_field = self.browser.find_element_by_id('login-password')
    submit = self.browser.find_element_by_id('login-submit')
    chain = self.chain.move_to_element(user_field).click(user_field)
    chain.send_keys_to_element(user_field, username)
    chain.move_to_element(pass_field).click(pass_field)
    chain.send_keys_to_element(pass_field, password)
    chain.move_to_element(submit).click(submit)
    chain.perform()

  def _visit_links(self):
    """Visit links offered by page."""
    links = self.browser.find_elements_by_css_selector(
        '#post-wrapper .panel-body a')
    urls = [link.get_attribute('href') for link in links]
    for url in urls:
      if url in self.visited:
        continue
      print 'Loading %s' % url
      self.browser.get('about:blank')
      self.browser.get(url)
      self.visited.add(url)
      # Better make their attacks fast!
      time.sleep(2)


if __name__ == '__main__':
  client = PwnTalkClient(chromedriver_path='/opt/chromedriver')
  client.start()

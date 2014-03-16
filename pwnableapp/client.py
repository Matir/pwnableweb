import os
import sys
import threading
import time
import xvfbwrapper
from selenium import webdriver
from selenium.common.exceptions import TimeoutException


class VulnerableClient(object):
  """Run a Chrome client to simulate XSS, XSRF, etc.

  Runs Chrome inside XVFB.  Only need to override run().
  """

  def __init__(self, chromedriver_path='chromedriver'):
    self.xvfb = xvfbwrapper.Xvfb(width=1024, height=768)
    self.xvfb.start()
    self.browser = webdriver.Chrome(executable_path=chromedriver_path)
    self._run_event = threading.Event()
    self._run_event.set()
    self._stop_event = threading.Event()
    self._stop_event.clear()
    self._thread = None

    # Get rid of stdin
    os.close(sys.stdin.fileno())

  def __del__(self):
    # Attempt to shutdown xvfb and browser
    try:
      if self.browser:
        self.browser.quit()
      if self.xvfb:
        self.xvfb.stop()
    except AttributeError:
      pass

  def start(self, check_interval=60):
    """Manage running the run() function.

    Calls run at check_interval seconds, unless run returns True, which
    reschedules it immediately.
    """
    self._thread = threading.Thread(target=self._wrap_run)
    self._thread.start()
    try:
      while True:
        time.sleep(check_interval)
        self._run_event.set()
    except KeyboardInterrupt:
      print 'Saw CTRL-C, shutting down.'
      self._stop_event.set()
      self._thread.join()
      self.browser.quit()
      self.browser = None
      self.xvfb.stop()
      self.xvfb = None

  def _wrap_run(self):
    """Run in a separate thread."""
    while not self._stop_event.is_set():
      if not self._run_event.wait(5):
        continue
      self._run_event.clear()
      try:
        while self.run():
          if self._stop_event.is_set():
            break
      except TimeoutException:
        continue

  def run(self):
    raise NotImplementedError("Must be implemented by subclass.")

  @property
  def chain(self):
    return webdriver.ActionChains(self.browser)

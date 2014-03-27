import argparse
import daemonize
import os
import signal
import sys
import threading
import time
import xvfbwrapper
from selenium import webdriver
from selenium.common import exceptions


class VulnerableClient(object):
  """Run a Chrome client to simulate XSS, XSRF, etc.

  Runs Chrome inside XVFB.  Only need to override run().
  """

  def __init__(self, name, chromedriver_path='chromedriver'):
    # Setup objects
    self._run_event = threading.Event()
    self._stop_event = threading.Event()
    self._thread = None
    self._chromedriver_path = chromedriver_path
    self._daemon = None
    self._name = name
    self._started = False

    # Parse config
    self._config = self._parse_config()
    if self._config.daemon:
      user = self._config.user if os.geteuid() == 0 else None
      group = self._config.group if os.geteuid() == 0 else None
      self._daemon = daemonize.Daemonize(
          name,
          pid=self._config.pidfile,
          action=self._start_internal,
          user=user,
          group=group)

  def _parse_config(self):
    parser = argparse.ArgumentParser(description='Vulnerable Client')
    parser.add_argument('--user', help='Drop privileges to this user.',
        default='nobody')
    parser.add_argument('--group', help='Drop privileges to this group.',
        default='nogroup')
    parser.add_argument('--nodaemon', help='Daemonize.', action='store_false',
        dest='daemon')
    parser.add_argument('--pidfile', help='Write pid to file.',
        default='/tmp/%s.pid' % self._name)
    return parser.parse_args()

  def __del__(self):
    # Attempt to shutdown xvfb and browser
    self.stop()

  def stop(self, *unused_args):
    if not self._started:
      return
    try:
      self._stop_event.set()
      if self._thread:
        self._thread.join()
      self.browser.quit()
      self.browser = None
      self.xvfb.stop()
      self.xvfb = None
    except AttributeError:
      pass
    sys.exit(0)

  def start(self, check_interval=60):
    """Manage running the run() function.

    Calls run at check_interval seconds, unless run returns True, which
    reschedules it immediately.
    """
    self._interval = check_interval
    if self._daemon:
      self._daemon.start()
    else:
      self._start_internal()

  def _start_internal(self):
    self._started = True
    # Signals
    for sig in (signal.SIGINT, signal.SIGQUIT, signal.SIGTERM):
      signal.signal(sig, self.stop)

    # Setup the browser & xvfb
    self.xvfb = xvfbwrapper.Xvfb(width=1024, height=768)
    self.xvfb.start()
    self.browser = webdriver.Chrome(executable_path=self._chromedriver_path)
    self._run_event.set()
    self._stop_event.clear()


    self._thread = threading.Thread(target=self._wrap_run)
    self._thread.start()
    try:
      while True:
        time.sleep(self._interval)
        self._run_event.set()
    except KeyboardInterrupt:
      print 'Saw CTRL-C, shutting down.'
      self.stop()

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
      except exceptions.WebDriverException:
        continue

  def run(self):
    raise NotImplementedError("Must be implemented by subclass.")

  @property
  def chain(self):
    return webdriver.ActionChains(self.browser)

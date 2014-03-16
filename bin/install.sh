#!/bin/bash
set -o noclobber
set -o errexit
set -o nounset
# For debugging
set -o xtrace

# Options
DESTDIR=/opt/pwnableweb
DRIVERDEST=/opt/chromedriver
# End options

if [ `id -u` -ne 0 ]; then
  echo "Must be run as root."
  exit 1
fi

function randpw() {
  dd if=/dev/urandom bs=16 count=1 2>/dev/null | base64
}
function randkey() {
  dd if=/dev/urandom bs=48 count=1 2>/dev/null | base64
}

# Get input
echo -n "Domain to run on: "
read DOMAIN
echo -n "MySQL Root password: "
read -s MYSQLPASS
# End input

if [[ `arch` == *64 ]] ; then
  CHROME=https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
  DRIVER=https://chromedriver.storage.googleapis.com/2.9/chromedriver_linux64.zip
else
  CHROME=https://dl.google.com/linux/direct/google-chrome-stable_current_i386.deb
  DRIVER=https://chromedriver.storage.googleapis.com/2.9/chromedriver_linux32.zip
fi

# Are we including scoreboard
if [ -d scoreboard ] ; then
  SCOREBOARD=true
else
  SCOREBOARD=false
fi

# Install prerequisites
# TODO: Support other platforms
apt-get update
# Probably should include current selections?
sudo debconf-set-selections <<EOFSELECTIONS
mysql-server mysql-server/root_password password $MYSQLPASS
mysql-server mysql-server/root_password_again password $MYSQLPASS
EOFSELECTIONS
apt-get -y install python-pip python-dev mysql-server libmysqlclient-dev xvfb \
  curl unzip build-essential nginx
curl -s -o /tmp/chrome.deb $CHROME
dpkg -i /tmp/chrome.deb && apt-get -fy install
curl -s -o /tmp/chromedriver.zip $DRIVER
unzip -d /tmp /tmp/chromedriver.zip
mkdir -p `dirname $DRIVERDEST`
mv /tmp/chromedriver $DRIVERDEST

# Setup virtualenv
pip install virtualenv
mkdir -p $DESTDIR
virtualenv $DESTDIR
set +o nounset
source $DESTDIR/bin/activate
set -o nounset

# Copy over
cp -rn `dirname $0`/.. $DESTDIR
cd $DESTDIR
mkdir sandbox

# Build sandbox binary
gcc -o sandbox/cmdwrapper pwntalk/tools/cmdwrapper.c

# Install virtualenv requirements
pip install flask sqlalchemy Flask-SQLAlchemy MySQL-python selenium \
  xvfbwrapper pbkdf2 gunicorn

# Setup users and groups
groupadd -f pwnableweb
usermod -a -G pwnableweb www-data
useradd -g pwnableweb -d $DESTDIR/pwncart -s /bin/nologin -M pwncart || \
  getent passwd pwncart
useradd -g pwnableweb -d $DESTDIR/pwntalk -s /bin/nologin -M pwntalk || \
  getent passwd pwntalk
useradd -g pwnableweb -d $DESTDIR/sandbox -s /bin/nologin -M sandbox || \
  getent passwd sandbox
$SCOREBOARD && ( useradd -g pwnableweb -d $DESTDIR/scoreboard -s /bin/nologin \
  -M scorebard || \
  getent passwd scoreboard )

# MySQL setup
PERMS="ALTER,CREATE,INDEX,DELETE,INSERT,SELECT,UPDATE"
PCPASS=`randpw`
PTPASS=`randpw`
SBPASS=`randpw`
mysql -uroot -p${MYSQLPASS} <<MYSQLEOF
CREATE DATABASE pwncart;
GRANT $PERMS ON pwncart.* TO 'pwncart'@'localhost' IDENTIFIED BY '${PCPASS}';
CREATE DATABASE pwntalk;
GRANT $PERMS ON pwntalk.* TO 'pwntalk'@'localhost' IDENTIFIED BY '${PTPASS}';
MYSQLEOF
$SCOREBOARD && mysql -uroot -p${MYSQLPASS} <<MYSQLEOF
CREATE DATABASE scoreboard;
GRANT $PERMS ON scoreboard.* TO 'scoreboard'@'localhost' IDENTIFIED BY '${SBPASS}';
MYSQLEOF
unset PERMS

# Write configs
cat >pwncart/config.py <<CONFIGEOF
SERVER_NAME='pwncart.${DOMAIN}'
SECRET_KEY='`randkey`'
SQLALCHEMY_DATABASE_URI='mysql://pwncart:${PCPASS}@localhost/pwncart'
CONFIGEOF
cat >pwntalk/config.py <<CONFIGEOF
SERVER_NAME='pwntalk.${DOMAIN}'
SECRET_KEY='`randkey`'
SQLALCHEMY_DATABASE_URI='mysql://pwntalk:${PTPASS}@localhost/pwntalk'
SANDBOX_BIN='$DESTDIR/sandbox/cmdwrapper'
CONFIGEOF
$SCOREBOARD && cat >scoreboard/config.py <<CONFIGEOF
SERVER_NAME='scoreboard.${DOMAIN}'
SECRET_KEY='`randkey`'
SQLALCHEMY_DATABASE_URI='mysql://scoreboard:${SBPASS}@localhost/scoreboard'
CONFIGEOF

# Set permissions
chgrp -R pwnableweb $DESTDIR
chown -R pwncart $DESTDIR/pwncart
chown -R pwntalk $DESTDIR/pwntalk
chown -R sandbox $DESTDIR/sandbox
$SCOREBOARD && chown -R scoreboard $DESTDIR/scoreboard
chmod -R ug-w,o-rwx $DESTDIR
chmod -R u-w,g-rw,o-rwx $DESTDIR/{pwncart,pwntalk}
chmod -R g+rX $DESTDIR/{pwncart,pwntalk}/static
chmod -R ug-w,o-rwx $DESTDIR/sandbox
chmod 4550 $DESTDIR/sandbox/cmdwrapper
$SCOREBOARD && chmod -R u-w,go-rwx $DESTDIR/scoreboard

# Setup webserver & appservers
cat >/etc/init.d/pwnableweb <<EOFSCRIPT
#!/bin/bash
# This script manages pwnableweb appservers.

export PYTHONPATH=$DESTDIR
source $DESTDIR/bin/activate

function start() {
  mkdir -p /var/run/pwnableweb
  chgrp pwnableweb /var/run/pwnableweb
  chmod 0750 /var/run/pwnableweb

  cd $DESTDIR
  mkdir -p $DESTDIR/logs
  # TODO: common settings in config
  bin/gunicorn -b 'unix:/var/run/pwnableweb/pwncart.sock' \
    -w 4 -D -u pwncart -g pwnableweb -p /var/run/pwnableweb/pwncart.pid \
    --access-logfile $DESTDIR/logs/pwncart.access.log \
    --error-logfile $DESTDIR/logs/pwncart.error.log \
    -m 007 pwncart.app:app
  bin/gunicorn -b 'unix:/var/run/pwnableweb/pwntalk.sock' \
    -w 4 -D -u pwntalk -g pwnableweb -p /var/run/pwnableweb/pwntalk.pid \
    --access-logfile $DESTDIR/logs/pwntalk.access.log \
    --error-logfile $DESTDIR/logs/pwntalk.error.log \
    -m 007 pwntalk.app:app
  if $SCOREBOARD ; then
    bin/gunicorn -b 'unix:/var/run/pwnableweb/scoreboard.sock' \
      -w 4 -D -u scoreboard -g pwnableweb -p /var/run/pwnableweb/scoreboard.pid \
      --access-logfile $DESTDIR/logs/scoreboard.access.log \
      --error-logfile $DESTDIR/logs/scoreboard.error.log \
      -m 007 scoreboard.app:app
  fi
  # Start clients
  python $DESTDIR/pwntalk/client.py >$DESTDIR/logs/pwntalk.client.log 2>&1 &
  echo \$! > /var/run/pwnableweb/pwntalk.client.pid
  python $DESTDIR/pwncart/client.py >$DESTDIR/logs/pwncart.client.log 2>&1 &
  echo \$! > /var/run/pwnableweb/pwncart.client.pid
}

function stop() {
  kill \`cat /var/run/pwnableweb/*.pid\`
}

function reload() {
  kill -HUP \`cat /var/run/pwnableweb/*.pid\`
}

case \$1 in
  start)
    start
    ;;
  stop)
    stop
    ;;
  restart)
    stop
    start
    ;;
  reload)
    reload
    ;;
  *)
    echo "Unknown command \$1!" >&2
    exit 1
    ;;
esac
EOFSCRIPT

chmod 700 /etc/init.d/pwnableweb
update-rc.d pwnableweb defaults

# Nginx setup
sed -i -r 's/^(\s*user\s+[A-Za-z0-9-]+).*$/\1 pwnableweb;/' \
  /etc/nginx/nginx.conf
cp -n etc/pwnableweb.nginx.conf /etc/nginx/sites-enabled/pwnableweb.conf
sed -i -e "s|\\\$DOMAIN|$DOMAIN|g" -e "s|\\\$DESTDIR|$DESTDIR|g" \
  /etc/nginx/sites-enabled/pwnableweb.conf
$SCOREBOARD && (
  cp -n etc/scoreboard.nginx.conf /etc/nginx/sites-enabled/scoreboard.conf;
  sed -i -e "s|\\\$DOMAIN|$DOMAIN|g" -e "s|\\\$DESTDIR|$DESTDIR|g" \
    /etc/nginx/sites-enabled/scoreboard.conf )

# Setup DBs
export PYTHONPATH=$DESTDIR
python pwntalk/main.py createdb
python pwncart/main.py createdb
$SCOREBOARD && python scoreboard/main.py createdb

# Start things
/etc/init.d/pwnableweb start
/etc/init.d/nginx restart

echo "If you got this far, everything completed successfully."

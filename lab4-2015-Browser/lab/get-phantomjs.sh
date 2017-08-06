#!/bin/sh

# Download and install phantomjs; the version on Debian doesn't work with the
# grading scripts, since it's missing phantom.clearCookies(), has some kind of
# broken require(), and other fun things.
# https://repo1.maven.org/maven2/com/github/klieber/phantomjs/1.9.2/phantomjs-1.9.2-linux-i686.tar.bz2
PHANTOMJS=phantomjs-1.9.2-linux-i686
if [ ! -e "$HOME/phantomjs" ]; then
  echo "One moment, downloading PhantomJS..."
  TEMPFILE=$(mktemp)
  TEMPDIR=$(mktemp -d)
  curl "https://repo1.maven.org/maven2/com/github/klieber/phantomjs/1.9.2/$PHANTOMJS.tar.bz2" > "$TEMPFILE"
  echo "Unpacking..."
  tar -C "$TEMPDIR" -xjf "$TEMPFILE"
  mv "$TEMPDIR/$PHANTOMJS/bin/phantomjs" "$HOME"
  # Cleanup
  rm "$TEMPFILE"
  rm -rf "$TEMPDIR"
  echo "Done"
fi

#!/bin/sh

# Download and install phantomjs; the version on Debian doesn't work with the
# grading scripts, since it's missing phantom.clearCookies(), has some kind of
# broken require(), and other fun things.
PHANTOMJS=phantomjs-1.9.2-linux-i686
if [ ! -e "$HOME/phantomjs" ]; then
  echo "One moment, downloading PhantomJS..."
  TEMPFILE=$(mktemp)
  TEMPDIR=$(mktemp -d)
  curl "http://phantomjs.googlecode.com/files/$PHANTOMJS.tar.bz2" > "$TEMPFILE"
  echo "Unpacking..."
  tar -C "$TEMPDIR" -xjf "$TEMPFILE"
  mv "$TEMPDIR/$PHANTOMJS/bin/phantomjs" "$HOME"
  # Cleanup
  rm "$TEMPFILE"
  rm -rf "$TEMPDIR"
  echo "Done"
fi

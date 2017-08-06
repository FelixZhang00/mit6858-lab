#!/bin/sh

./get-phantomjs.sh

SANDBOXHTML=/tmp/sb.$$.html

for P in ./profiles/good-*.html ./profiles/bad-*.html; do
  echo "------------------------------------------------"
  echo "Profile: $P"

  if ./zoobar/filter-test.py <$P >$SANDBOXHTML; then
    $HOME/phantomjs test-profile.js "$SANDBOXHTML"
  else
    echo "Sandbox: rewriter error"
  fi
done

rm -f $SANDBOXHTML


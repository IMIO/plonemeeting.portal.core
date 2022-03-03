#!/bin/bash
URL="http://localhost:20081/demo"
CURL="curl --write-out %{http_code} -so /dev/null $URL/@@ok"
MAX_TRIES=240
INTERVAL=1
SECONDS=0
response="$($CURL)"
tries=1
while [[ $response != "200" && $tries -lt $MAX_TRIES ]]
do
  sleep $INTERVAL
  response=$($CURL)
  ((tries+=1))
done
if [[ $tries == "$MAX_TRIES" ]]; then
  echo "Failed to reach $URL after $SECONDS s"
  exit 1
else
  echo "$URL is up. Waited $SECONDS s"
fi

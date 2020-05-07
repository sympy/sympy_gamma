#!/usr/bin/env bash

HOST="0.0.0.0"
API_PORT="8082"
ADMIN_PORT="8083"
DATASTORE_EMULATOR_HOST_PORT=datastore:8081

python $SDK_LOCATION/dev_appserver.py --api_host 0.0.0.0 \
 --api_port "$API_PORT" \
 --admin_host "$HOST" \
 --admin_port "$ADMIN_PORT" \
 --host "$HOST" \
 --skip_sdk_update_check 1 . \
 --env_var DATASTORE_EMULATOR_HOST="$DATASTORE_EMULATOR_HOST_PORT" \
 --env_var DATASTORE_USE_PROJECT_ID_AS_APP_ID=true

#!/usr/bin/env bash

unset CDPATH;
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )";

########################################################################
#
# shutdown ()
#
# signal handler, kills jobs and exits
#
########################################################################

function shutdown () {
    echo "Received SIGINT or SIGTERM. Shutting down $DAEMON"
    exit 1;
}

# setup signal trapping
# shutdown if we get the following signals
trap shutdown SIGINT SIGTERM

# Make sure the directory for individual app logs exists
mkdir -p /var/log/shiny-server
chown shiny.shiny /var/log/shiny-server

# start shiny-server
exec shiny-server >> /var/log/shiny-server.log 2>&1

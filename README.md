Cabot MSTeams Plugin
=====

This is an alert plugin for the Cabot service monitoring tool. It allows you to send alerts to an MS Teams channel.

## Installation

Extend Dockerfile based on cabotapp/cabot:0.11.16

- RUN apk add --no-cache git
- RUN pip install https://github.com/ngc4579/cabot-alert-msteams

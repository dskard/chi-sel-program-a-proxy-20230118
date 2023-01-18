"""Process individual messages from a WebSocket connection."""
# modified
# https://github.com/mitmproxy/mitmproxy/blob/5df439b7e8e90e7e889163cab4a7d15fafd91ce2/examples/addons/websocket-simple.py
import logging
import re

from mitmproxy import http


class RewriteWebsocketMessage:
    def __init__(self):
        pass

    def websocket_message(self, flow: http.HTTPFlow):
        assert flow.websocket is not None

        # get the latest message
        message = flow.websocket.messages[-1]

        if message.from_client is True:
            # manipulate the message content
            # when the message says to use 20 bins, replace it with 5 bins
            pattern = rb'{\\"method\\":\\"update\\",\\"data\\":{\\"bins\\":20}}'
            replacement = rb'{\\"method\\":\\"update\\",\\"data\\":{\\"bins\\":5}}'

            if re.search(pattern, message.content) is not None:
                message.content = re.sub(pattern, replacement, message.content)
                logging.info(f"updated message: {message.content!r}")


addons = [RewriteWebsocketMessage()]

import logging
import re

from mitmproxy import http


class SwitchWTTRCities:
    def __init__(self):
        self.num = 0

    def request(self, flow: http.HTTPFlow) -> None:
        # look in the request's url path for "Chicago"
        if re.search(r"Chicago", flow.request.path) is not None:
            # replace "Chicago" with "Dallas"
            flow.request.path = re.sub(r"Chicago", "Dallas", flow.request.path)
            logging.info("Changing city from Chicago to Dallas")


addons = [SwitchWTTRCities()]

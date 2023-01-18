#!/usr/bin/env python3

import atexit
import copy
import manageritm
import re
import pprint
import socket
import sys
import systemstat

from mitmweb_client import MitmWebClient
from selene.api import browser, have
from selenium import webdriver
from selenium.common.exceptions import WebDriverException


def atexit_stop_proxy_server(mc):
    """stop the mitmproxy server
    """

    mc.proxy_stop()


pp = pprint.PrettyPrinter(indent=4)

manageritm_addr = "chisel_manageritm-server_1"
manageritm_port = "8000"
selenium_hub = "chisel_selenium-hub_1"
selenium_port = "4444"

# create a manageritm client
mc = manageritm.client.ManagerITMClient(f'http://{manageritm_addr}:{manageritm_port}')
proxy_details = mc.client(port=5200, webport=5201)

print(f"proxy port: {proxy_details['port']}")
print(f"proxy webport: {proxy_details['webport']}")

mitmweb_ip = socket.gethostbyname(manageritm_addr)
mitmweb_proxy_url = f"http://{mitmweb_ip}:{proxy_details['port']}"
mitmweb_web_url = f"http://{mitmweb_ip}:{proxy_details['webport']}"
proxies = {
    'http': mitmweb_proxy_url,
    'https': mitmweb_proxy_url
}

# start a proxy server
mc.proxy_start()
atexit.register(atexit_stop_proxy_server, mc)

# wait for the proxy server to be ready
systemstat.SutStat(mitmweb_web_url).wait_until_ready()

# setup a MitmWebClient
# make sure the mitmweb client traffic also uses our proxy.
mwc = MitmWebClient(mitmweb_web_url, proxies=proxies)

# configure the web browser to talk to the proxy server
# more info on options at:
# https://www.selenium.dev/documentation/webdriver/capabilities/shared/
options = webdriver.firefox.options.Options()
options.set_preference('network.proxy.type', 1)
options.set_preference('network.proxy.http', manageritm_addr)
options.set_preference('network.proxy.http_port', proxy_details["port"])
options.set_preference('network.proxy.ssl', manageritm_addr)
options.set_preference('network.proxy.ssl_port', proxy_details["port"])
options.set_preference('network.proxy.socks', manageritm_addr)
options.set_preference('network.proxy.socks_port', proxy_details["port"])
options.set_preference('network.proxy.socks_remote_dns', False)

# launch the web browser
driver = webdriver.Remote(
    command_executor=f"http://{selenium_hub}:{selenium_port}/wd/hub",
    options=options,
)

# tell selene about the web browser
browser.config.driver = driver

# navigate to the duckduckgo website
url = "https://ddg.gg"
browser.open(url)

# check the status code from mitmweb client
mwc.execute_command("view.filter.set", ["~m GET & ~u duckduckgo.com/$ & ~c 200 & ! ~a"])
flows = mwc.get_flows()
pp.pprint(flows)
assert len(flows) >= 1
assert flows[0]['response']['status_code'] == 200

# show all flows again
mwc.execute_command("view.filter.set", [f""])

# set an intercept for a request querying "rstudio"
new_options = {'intercept': "~m GET & ~u https://duckduckgo.com/\\?q=rstudio & ~q"}
mwc.update_options(new_options)

# type rstudio in the search box and press enter
browser.element("#search_form_input_homepage")\
    .type("rstudio")\
    .press_enter()

# retrieve the intercepted flow from the proxy
mwc.execute_command("view.filter.set", ["~m GET & ~u https://duckduckgo.com/\\?q=rstudio & ~q"])
flows = mwc.get_flows()
assert len(flows) == 1

# modify the request, replacing "rstudio" with "posit"
new_path = re.sub("rstudio", "posit", flows[0]['request']['path'])
flow_request = {'request': {'path': new_path}}
mwc.update_flow(flows[0]['id'], flow_request)

# resume the flow
mwc.resume_flow(flows[0]['id'])

# show all flows again
mwc.execute_command("view.filter.set", [f""])

# check that there is a search box now has "posit"
browser.element("#search_form_input")\
    .should(have.attribute('value').value("posit"))

# remove the intercept
new_options = {'intercept': ""}
mwc.update_options(new_options)

# close the browser
try:
    driver.quit()
except WebDriverException:
    # connection to browser was closed
    # probably due to timeout from being inactive
    # need to manually close the browser
    print("failed to close web browser")

# stop the proxy server
mc.proxy_stop()
atexit.unregister(atexit_stop_proxy_server)

print(f"har file path: {proxy_details['har']}")

# exit
sys.exit(0)

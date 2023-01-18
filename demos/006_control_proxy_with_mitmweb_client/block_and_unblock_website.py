#!/usr/bin/env python3

import atexit
import copy
import manageritm
import pprint
import socket
import sys
import systemstat

from mitmweb_client import MitmWebClient
from selene.api import browser
from selenium import webdriver
from selenium.common.exceptions import WebDriverException


def atexit_stop_proxy_server(mc):
    """stop the proxy server
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

# navigate to the rstudio website
url = "https://posit.co"
browser.open(url)

# check the status code from mitmweb client
# maybe a filter like:
# [f"~m GET & ~u {url}"]
# ["~m GET & ~d posit.co & ~c 200 & ! ~a"]
mwc.execute_command("view.filter.set", ["~m GET & ~d posit.co & ~c 200 & ! ~a & ! ~u cookie_data"])
flows = mwc.get_flows()
pp.pprint(flows)
assert len(flows) == 1
assert flows[0]['response']['status_code'] == 200

# show all flows again
mwc.execute_command("view.filter.set", [f""])

# get the options:
opts = mwc.get_options()
pp.pprint(opts['block_list']['value'])

# setup new options
block_list = copy.deepcopy(opts['block_list']['value'])
new_options = {'block_list': copy.deepcopy(opts['block_list']['value'])}
new_options['block_list'].append(":~d posit\.co:444")

# send the new options to the server
mwc.update_options(new_options)

# refresh the web browser, rstudio should be blocked
# catch the exception thrown when the request fails
try:
    browser.driver.refresh()
except WebDriverException:
    pass

# check that the request was blocked
# it should be caught by an error filter with `~e`
# could probably also use the `~q` filter, no response
# grab the most recent (last) flow matching the filter
mwc.execute_command("view.filter.set", ["~m GET & ~d posit.co & ~e & ! ~a & ! ~u cookie_data"])
flows = mwc.get_flows()
pp.pprint(flows)
assert len(flows) >= 1
assert flows[-1]['error']['msg'] == "Connection killed."

# update options again, removing rstudio from blocklist
new_options = {'block_list': copy.deepcopy(block_list)}
mwc.update_options(new_options)

# refresh the web browser, rstudio should not be blocked
browser.driver.refresh()

# check the status code from mitmweb client
# there should be 2 successful flows that match the filter now
# grab the most recent flow (latest flow)
mwc.execute_command("view.filter.set", ["~m GET & ~d posit.co & ~c 200 & ! ~a & ! ~u cookie_data"])
flows = mwc.get_flows()
pp.pprint(flows)
assert len(flows) == 2
assert flows[-1]['response']['status_code'] == 200

# show all flows again
mwc.execute_command("view.filter.set", [f""])

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

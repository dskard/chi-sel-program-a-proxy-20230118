#!/usr/bin/env python3

import manageritm
import sys
import time

from selenium import webdriver
from selenium.common.exceptions import WebDriverException

manageritm_addr = "chisel_manageritm-server_1"
manageritm_port = "8000"
selenium_hub = "chisel_selenium-hub_1"
selenium_port = "4444"

# create a manageritm client
mc = manageritm.client.ManagerITMClient(f'http://{manageritm_addr}:{manageritm_port}')
proxy_details = mc.client()

print(f"proxy port: {proxy_details['port']}")
print(f"proxy webport: {proxy_details['webport']}")

# start a proxy server
mc.proxy_start()

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

# wait for a user interrupt
while True:
    try:
        # keep the browser alive by interacting with the browser.
        # interact every 250 seconds.
        # selenium grid default --session-timeout is 300 seconds.
        driver.title
        time.sleep(250)
    except:
        break

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

print(f"har file path: {proxy_details['har']}")

# exit
sys.exit(0)

#!/usr/bin/env python3

import argparse
import logging
import sys
import time

from selenium import webdriver

log = logging.getLogger(__name__)

def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--browser",
        help='type of web browser, chrome or firefox',
        default="firefox",
        type=str,
    )

    parser.add_argument(
        "--no-proxy",
        help='use a proxy',
        action='store_true',
        default=False
    )

    parser.add_argument(
        "--proxy-addr",
        help='hostname of the proxy',
        default="chisel_mitmproxy",
        type=str,
    )

    parser.add_argument(
        "--proxy-port",
        help='port of the proxy',
        default=8080,
        type=int,
    )

    parser.add_argument(
        "--selenium-addr",
        help='hostname of the selenium grid hub',
        default="chisel_selenium-hub_1",
        type=str,
    )

    parser.add_argument(
        "--selenium-port",
        help='port of the selenium grid hub',
        default=4444,
        type=int,
    )

    parser.add_argument(
        "--verbose",
        "-v",
        help="level of logging verbosity",
        default=3,
        action="count",
    )

    opts = parser.parse_args()
    return opts


def setup_firefox_options(opts):
    options = webdriver.firefox.options.Options()

    if opts.no_proxy is False:
        options.set_preference('network.proxy.type', 1)
        options.set_preference('network.proxy.http', opts.proxy_addr)
        options.set_preference('network.proxy.http_port', opts.proxy_port)
        options.set_preference('network.proxy.ssl', opts.proxy_addr)
        options.set_preference('network.proxy.ssl_port', opts.proxy_port)

    capabilities = webdriver.DesiredCapabilities.FIREFOX.copy()
    capabilities['acceptInsecureCerts'] = True

    return options, capabilities


def setup_chrome_options(opts):
    options = webdriver.chrome.options.Options()

    if opts.no_proxy is False:
        options.add_argument(f'--proxy-server={opts.proxy_addr}:{opts.proxy_port}')

    options.add_argument(f'--disable-notifications')

    capabilities = webdriver.DesiredCapabilities.CHROME.copy()
    capabilities['acceptInsecureCerts'] = True

    return options, capabilities


def main():

    opts = parse_arguments()

    logging.basicConfig(level=int((6 - opts.verbose) * 10))

    log.debug("opts = {}".format(opts))

    # configure the web browser to talk to the proxy server
    # more info on options at:
    # https://www.selenium.dev/documentation/webdriver/capabilities/shared/
    if opts.browser == "firefox":
        options, capabilities = setup_firefox_options(opts)
    elif opts.browser == "chrome":
        options, capabilities = setup_chrome_options(opts)
    else:
        log.error(f"using browser type {opts.browser} is unsupported. choose from 'firefox' or 'chrome'")

    # launch a web browser
    driver = webdriver.Remote(
        command_executor=f"http://{opts.selenium_addr}:{opts.selenium_port}/wd/hub",
        desired_capabilities=capabilities,
        options=options,
    )

    driver.maximize_window()

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
    driver.quit()

    log.debug("exiting")

    return 0

if __name__ == "__main__":

    status = main()

    sys.exit(status)

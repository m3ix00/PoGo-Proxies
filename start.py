#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import logging

from proxytools.proxy_tester import check_proxies, get_local_ip
from proxytools.proxy_scrapper import (scrap_sockslist_net,
                                       scrap_vipsocks24_net,
                                       scrap_proxyserverlist24_top)
from proxytools import utils

logging.getLogger("requests").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.basicConfig(
    format='%(asctime)s [%(threadName)15.15s][%(levelname)8.8s] %(message)s',
    level=logging.INFO)
log = logging.getLogger('pogo-proxies')


def work_cycle(args):
    proxies = set()
    if args.proxy_file:
        log.info('Loading proxies from file: %s', args.proxy_file)
        proxylist = utils.load_proxies(args.proxy_file, args.mode)

        if len(proxylist) > 0:
            proxies.update(proxylist)
        else:
            log.error('Proxy file was configured but no proxies were loaded.')
            sys.exit(1)
    else:
        if args.mode == 'http':
            log.info('Scrapping HTTP proxies...')
            proxies.update(scrap_proxyserverlist24_top())
        else:
            log.info('Scrapping SOCKS5 proxies...')
            proxies.update(scrap_sockslist_net(args.ignore_country))
            proxies.update(scrap_vipsocks24_net())

    proxies = list(proxies)

    if args.no_test:
        output(args, proxies)
        return

    args.local_ip = None
    if not args.no_anonymous:
        local_ip = get_local_ip(args.proxy_judge)

        if not local_ip:
            log.error('Failed to identify local IP address.')
            sys.exit(1)

        log.info('Local IP address: %s', local_ip)
        args.local_ip = local_ip

    log.info('Found a total of %d proxies. Starting tests...', len(proxies))
    if args.batch_size > 0:
        chunks = [proxies[x:x+args.batch_size]
                  for x in xrange(0, len(proxies), args.batch_size)]
        working_proxies = []
        for chunk in chunks:
            working_proxies.extend(check_proxies(args, chunk))
            output(args, working_proxies)
            if len(working_proxies) >= args.limit:
                break
    else:
        working_proxies = check_proxies(args, proxies)
        output(args, working_proxies)


def output(args, proxies):
    output_file = args.output_file
    log.info('Writing %d working proxies to: %s',
             len(proxies), output_file)

    if args.proxychains:
        utils.export_proxychains(output_file, proxies)
    elif args.kinancity:
        utils.export_kinancity(output_file, proxies)
    else:
        utils.export(output_file, proxies, args.clean)


if __name__ == '__main__':
    log.setLevel(logging.INFO)

    args = utils.get_args()
    working_proxies = []

    if args.verbose:
        log.setLevel(logging.DEBUG)
        log.debug('Running in verbose mode (-v).')

    work_cycle(args)

    sys.exit(0)

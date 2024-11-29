#!/usr/bin/env python3
import logging
from argparse import ArgumentParser

from walless_utils import Controller

logger = logging.getLogger('walless')


def run():
    parser = ArgumentParser()
    parser.add_argument('action', metavar='ACTION', choices=['sync', 'mix'])
    parser.add_argument('--src', metavar='SOURCE', type=int, help='Mix node id')
    parser.add_argument('--tgt', metavar='TARGET', type=int, help='Node id in cname')
    parser.add_argument(
        '--mix_type', choices=['edu', 'out', 'all'], type=str, help='edu, out, or all? default to all.',
        default='all'
    )
    args = parser.parse_args()

    ctl = Controller()

    if args.action == 'sync':
        ctl.sync_ip()
        ctl.sync_mix()
    elif args.action == 'mix':
        ctl.mix(args.src, args.tgt, args.mix_type)
    else:
        raise NotImplementedError


if __name__ == '__main__':
    run()

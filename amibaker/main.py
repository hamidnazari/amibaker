#!/usr/bin/env python

import argparse
from .version import VERSION
from .ami_baker import AmiBaker

def run_recipies(args, recipies):
    for recipe in recipies:
        baker = AmiBaker(recipe,
                         quiet=args.quiet,
                         keep_instance=args.keep_instance,
                         override_base_ami=args.base_ami,
                         specific_id=args.specific_id
                         )
        baker.bake()


def main():
    argparser = argparse.ArgumentParser()

    argparser.add_argument(
        'recipe',
        nargs='+',
        type=argparse.FileType('r'),
        help='Recipe to bake an image from.')

    argparser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Prevents messages from being printed to stdout.')

    argparser.add_argument(
        '-k', '--keep-instance',
        action='store_true',
        help='Keeps EC2 instance after provisioning is done.')

    argparser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s ' + VERSION,
        help='Shows version number.')

    argparser.add_argument(
        '-b', '--base-ami',
        action='store',
        help='Specify base_ami, supersedes any base_ami specified in recipe'
    )

    argparser.add_argument(
        '-u', '--specific_id',
        action='store',
        help='For testing recipes, id of an already running ec2 machine'
    )

    args = argparser.parse_args()
    run_recipies(args, args.recipe)


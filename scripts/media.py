#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script tools for generating media files related to the project.
"""
#
#   Imports
#
import os
import logging

import click
import dotenv


#
#   Globals
#

PROJECT_DIR = None
DATA_DIR = None
RAW_DIR = None
PROCESSED_DIR = None
INTERIM_DIR = None
COOKED_DIR = None
MEDIA_DIR = None


#
#   Setup
#

logger = logging.getLogger(__name__)
dotenv.load_dotenv()


#
#   Script Functions
#

@click.group()
@click.pass_context
def cli(ctx):
    """
    Tools for media files.
    """
    ctx.ensure_object(dict)


@cli.command()
@click.pass_context
def generate(ctx):
    """
    Tool(s) for generating media files.
    """
    # [START] Media file generation code here
    pass


#
#   Entry-point
#

if __name__ == "__main__":
    # - Configure logging
    log_fmt = '[%(levelname)s %(name)s %(asctime)s] %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # - Relevant paths
    PROJECT_DIR = os.path.join(os.path.dirname(__file__), os.pardir)
    DATA_DIR = os.path.join(PROJECT_DIR, 'data')
    RAW_DIR = os.path.join(DATA_DIR, 'raw')
    PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
    INTERIM_DIR = os.path.join(DATA_DIR, 'interim')
    COOKED_DIR = os.path.join(DATA_DIR, 'cooked')
    MEDIA_DIR = os.path.join(PROJECT_DIR, 'media')

    cli(obj={})

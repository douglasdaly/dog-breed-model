#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script tools for getting and processing the project's data.
"""
import os
import logging
import shutil
import tarfile
import xml.etree.ElementTree as ET
import zipfile

import click
import dotenv
from kaggle import api
from PIL import Image
from tqdm import tqdm


#
#   Globals
#

PROJECT_DIR = None
DATA_DIR = None
RAW_DIR = None
PROCESSED_DIR = None
INTERIM_DIR = None
COOKED_DIR = None


#
#   Setup
#

logger = logging.getLogger(__name__)
dotenv.load_dotenv()


#
#   Helpers
#

def get_annotations(path):
    """Gets the annotation data from the given path"""
    # Process the annotation data
    annots = {}
    for root, dirs, files in tqdm(os.walk(path), desc='Loading Annotations'):
        if not files and not os.path.basename(root).startswith('n'):
            continue
        p_data = {}
        p_data['folder'] = os.path.basename(root)
        p_data['files'] = {}
        p_name = None
        for file in files:
            t_data = {}
            t_xml = ET.parse(os.path.join(root, file)).getroot()
            for child in t_xml:
                if child.tag == 'size':
                    t_data['size'] = {}
                    for nchild in child:
                        t_data['size'][nchild.tag] = int(nchild.text)
                elif child.tag == 'object':
                    for nchild in child:
                        if not p_name and nchild.tag == 'name':
                            p_name = '_'.join([
                                x[0].upper() + x[1:]
                                for x in nchild.text.replace('_', ' ').split()
                            ])
                        elif nchild.tag == 'bndbox':
                            t_data['bbox'] = {}
                            for nnchild in nchild:
                                t_data['bbox'][nnchild.tag] = int(nnchild.text)
            p_data['files'][file.split('_')[-1]] = t_data
        annots[p_name] = p_data
    return annots


def process_images(src, dest, annotations):
    """Processes the source images based on the annotations given"""
    for breed, a_data in tqdm(annotations.items(), desc='Processing Images'):
        b_dir = os.path.join(dest, breed)
        if not os.path.exists(b_dir):
            os.mkdir(b_dir)
        src_base = os.path.join(src, a_data['folder'])
        for file in os.listdir(src_base):
            fname = os.path.splitext(file)[0]
            s_file = os.path.join(src_base, file)
            if fname not in a_data['files']:
                shutil.copy(s_file, b_dir)
            else:
                bbox = a_data['files'][fname]
                im = Image.open(s_file)
                im = im.crop(box=(bbox[x] for x in [
                    'xmin', 'ymax', 'xmax', 'ymin'
                ]))
                im.save(os.path.join(b_dir, file))
    return


#
#   Script commands
#

@click.group()
@click.pass_context
def cli(ctx):
    """
    Tools for acquiring and processing data.
    """
    ctx.ensure_object(dict)


@cli.command()
@click.pass_context
def get(ctx):
    """
    Tool for acquiring the raw data files.
    """
    api.dataset_download_files(
        'jessicali9530/stanford-dogs-dataset', path=RAW_DIR, quiet=False
    )
    return


@cli.command()
@click.pass_context
def process(ctx):
    """
    Tool for processing the raw data files.
    """
    zfile = zipfile.ZipFile(os.path.join(RAW_DIR, 'stanford-dogs-dataset.zip'))
    zfile.extractall(INTERIM_DIR)
    paths = zfile.namelist()
    for path in paths:
        with tarfile.open(os.path.join(INTERIM_DIR, path), 'r') as tfile:
            tfile.extractall(path=INTERIM_DIR)
        os.remove(os.path.join(INTERIM_DIR, path))

    annot_dir = os.path.join(INTERIM_DIR, 'Annotation')
    img_dir = os.path.join(INTERIM_DIR, 'Images')
    annots = get_annotations(annot_dir)
    process_images(img_dir, PROCESSED_DIR, annots)

    shutil.rmtree(annot_dir)
    shutil.rmtree(img_dir)
    return


@cli.command()
@click.pass_context
def cook(ctx):
    """
    Tool for cooking the processed data files.
    """
    # [START] Data cooking code here
    pass


#
#   Entry-point
#

if __name__ == "__main__":
    # - Configure logging
    log_fmt = '[%(levelname)s %(name)s %(asctime)s] %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # - Relevant paths
    PROJECT_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir)
    )
    DATA_DIR = os.path.abspath(os.path.join(PROJECT_DIR, 'data'))
    RAW_DIR = os.path.abspath(os.path.join(DATA_DIR, 'raw'))
    PROCESSED_DIR = os.path.abspath(os.path.join(DATA_DIR, 'processed'))
    INTERIM_DIR = os.path.abspath(os.path.join(DATA_DIR, 'interim'))
    COOKED_DIR = os.path.abspath(os.path.join(DATA_DIR, 'cooked'))

    # - Run Main Function
    cli(obj={})

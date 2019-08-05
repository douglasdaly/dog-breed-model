#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script tools for getting and processing the project's data.
"""
import os
import logging
import random
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
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

dotenv.load_dotenv()


#
#   Helpers
#

def get_annotations(path):
    """Gets the annotation data from the given path"""
    annots = {}
    for root, dirs, files in tqdm(os.walk(path), desc='Loading Annotations'):
        if not files and not os.path.basename(root).startswith('n'):
            continue
        p_data = {}
        p_data['folder'] = os.path.basename(root)
        p_data['files'] = {}
        p_name = None
        for file in files:
            t_data, p_name = process_annotation_file(
                os.path.join(root, file), breed_name=p_name
            )
            p_data['files'][file.split('_')[-1]] = t_data
        annots[p_name] = p_data
    return annots


def process_annotation_file(path, breed_name=None):
    """Loads/processes a single annotation XML file."""
    ret = {}
    root = ET.parse(path).getroot()
    for child in root:
        if child.tag == 'size':
            ret['size'] = {}
            for nchild in child:
                ret['size'][nchild.tag] = int(nchild.text)
        elif child.tag == 'object':
            for nchild in child:
                if not breed_name and nchild.tag == 'name':
                    breed_name = '_'.join([
                        x[0].upper() + x[1:]
                        for x in nchild.text.replace('_', ' ').split()
                    ])
                elif nchild.tag == 'bndbox':
                    ret['bbox'] = {}
                    for nnchild in nchild:
                        ret['bbox'][nnchild.tag] = int(nnchild.text)
    return ret, breed_name


def process_images(src, dest, annotations, test_size=0.10, seed=42):
    """Processes the source images based on the annotations given"""
    random.seed(seed)

    # Create the train/test directories in the data/processed folder
    train_dir = os.path.join(dest, 'train')
    test_dir = os.path.join(dest, 'test')
    if not os.path.exists(train_dir):
        os.mkdir(train_dir)
    if not os.path.exists(test_dir):
        os.mkdir(test_dir)

    # Loop over the breeds/annotation data and process the images
    for breed, a_data in tqdm(annotations.items(), desc='Processing Images'):
        # - Create the sub-directories for each breed
        train_bdir = os.path.join(train_dir, breed)
        test_bdir = os.path.join(test_dir, breed)
        if not os.path.exists(train_bdir):
            os.mkdir(train_bdir)
        if not os.path.exists(test_bdir):
            os.mkdir(test_bdir)

        # - Get the image files, select a sub-set for our test set
        src_base = os.path.join(src, a_data['folder'])
        src_files = sorted(os.listdir(src_base))
        test_files = random.sample(src_files, round(test_size*len(src_files)))
        for file in tqdm(src_files, desc=breed.replace('_', ' '), leave=False):
            # - Determine the train/test directory to use
            b_dir = test_bdir if file in test_files else train_bdir
            fname = os.path.splitext(file)[0].split('_')[-1]
            s_file = os.path.join(src_base, file)

            # - If we don't have annotation data for the particular file
            #   simply copy the image, otherwise crop it to the bounding
            #   box from the annotation data.
            d_file = os.path.join(b_dir, f'{breed}_{fname}.jpg')
            if fname not in a_data['files']:
                shutil.copy(s_file, d_file)
            else:
                bbox = a_data['files'][fname]['bbox']
                try:
                    crop_and_save(s_file, d_file, bbox)
                except Exception:
                    print()
                    disp_file = os.path.sep.join(os.path.split(s_file)[-2:])
                    logger.error(f"Could not crop image: {disp_file}")
                    raise
    return


def crop_and_save(src, dest, bbox):
    """Crops and saves the given image to the given destination."""
    try:
        im = Image.open(src).copy()
        im = im.convert("RGB")
        im = im.crop(box=(bbox[x] for x in [
            'xmin', 'ymin', 'xmax', 'ymax'
        ]))
        im.save(dest)
    except Exception:
        raise
    finally:
        im.close()
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
    Downloads the raw data files.
    """
    # Download the raw data using the kaggle API
    api.dataset_download_files(
        'jessicali9530/stanford-dogs-dataset', path=RAW_DIR, quiet=False
    )
    return


@cli.command()
@click.pass_context
@click.option('--test-size', default=0.10, show_default=True,
              help='Portion of images to use for test set')
@click.option('--seed', default=42, show_default=True,
              help='Random seed value to use in train/test split.')
def process(ctx, test_size, seed):
    """
    Processes the raw data files.
    """
    # Extract the zip file and the subsequent tar files
    zfile = zipfile.ZipFile(os.path.join(RAW_DIR, 'stanford-dogs-dataset.zip'))
    zfile.extractall(INTERIM_DIR)
    paths = zfile.namelist()
    for path in paths:
        with tarfile.open(os.path.join(INTERIM_DIR, path), 'r') as tfile:
            tfile.extractall(path=INTERIM_DIR)
        os.remove(os.path.join(INTERIM_DIR, path))

    # Load the annotation data and process the images
    annot_dir = os.path.join(INTERIM_DIR, 'Annotation')
    img_dir = os.path.join(INTERIM_DIR, 'Images')
    annots = get_annotations(annot_dir)
    process_images(
        img_dir, PROCESSED_DIR, annots, test_size=test_size, seed=seed
    )

    # Remove the (now un-needed) extracted data
    shutil.rmtree(annot_dir)
    shutil.rmtree(img_dir)
    return


@cli.command()
@click.pass_context
def cook(ctx):
    """
    Cooks the processed data files.
    """
    # [START] Data cooking code here
    pass


@cli.command()
@click.argument('path', type=click.STRING, nargs=-1, required=True)
@click.option('--output', type=click.STRING, default=None, 
              help='Output file to generate.')
@click.pass_context
def compress(ctx, path, output):
    """
    Compresses the specified paths into an archive.
    """
    if not output:
        output = 'archive.tar.gz'
    elif not output.endswith('.tar.gz'):
        output += '.tar.gz'
    
    with tarfile.open(output, 'w:gz') as archive:
        if len(path) > 1:
            path_iter = tqdm(path, desc='Paths Processed', leave=False)
        else:
            path_iter = path
        for p in path_iter:
            repl_nm, fld_nm = os.path.split(p)
            if os.path.isdir(p):
                all_files = {}
                for (rootdir, subdirs, files) in os.walk(p):
                    arch_rdir = rootdir.replace(repl_nm, '')
                    for f in files:
                        f_path = os.path.join(rootdir, f)
                        all_files[f_path] = os.path.join(arch_rdir, f)
                
                file_iter = tqdm(all_files.items(), desc=p, leave=False, 
                                 position=1)
                for fin, fout in file_iter:
                    archive.add(fin, fout)
            else:
                archive.add(p, p.replace(repl_nm, ''))
    
    print(f'Archive created: {output}')
    return


#
#   Entry-point
#

if __name__ == "__main__":
    PROJECT_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir)
    )
    DATA_DIR = os.path.abspath(os.path.join(PROJECT_DIR, 'data'))
    RAW_DIR = os.path.abspath(os.path.join(DATA_DIR, 'raw'))
    PROCESSED_DIR = os.path.abspath(os.path.join(DATA_DIR, 'processed'))
    INTERIM_DIR = os.path.abspath(os.path.join(DATA_DIR, 'interim'))
    COOKED_DIR = os.path.abspath(os.path.join(DATA_DIR, 'cooked'))

    cli(obj={})

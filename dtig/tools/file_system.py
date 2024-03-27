import os
import shutil
import subprocess

from dtig.common.logging import *
from zipfile import ZipFile
from urllib.request import urlretrieve
from dtig.common.result import VoidResult

def download_file(url : str, file : str) -> VoidResult:
    try:
        urlretrieve(url, file)
    except Exception as e:
        return VoidResult.failed(e.message)

    return VoidResult()

def extract_archive(in_file : str, out_dir : str) -> VoidResult:
    try:
        with ZipFile(in_file, 'r') as zObject:
            zObject.extractall(path=out_dir)
    except Exception as e:
        return VoidResult.failed(e.message)

    return VoidResult()

def copy_archive(src : str, dst : str) -> VoidResult:
    try:
        if os.path.isdir(src):
            LOG_DEBUG(f'Source: {src} is a directory')

            os.makedirs(os.path.dirname(dst), exist_ok=True)

            for filename in os.listdir(src):
                source_file = os.path.join(src, filename)
                destination_file = os.path.join(dst, filename)

                LOG_DEBUG(f'Copying {source_file} to {destination_file}')
                if os.path.isfile(source_file):
                    shutil.copy(source_file, destination_file)
                else:
                    shutil.copytree(source_file, destination_file)

        elif os.path.isdir(dst):
            LOG_DEBUG(f'Destination {dst} is a directory')
            source_file = os.path.basename(src)
            destination_file = os.path.join(dst, source_file)
            shutil.copy(src, destination_file)
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(src, dst)
    except Exception as e:
        return VoidResult.failed(e.message)

    return VoidResult()
import tarfile
import os
from time import time
from json import dumps
from io import BytesIO
from gzip import GzipFile
from pathlib import Path
from dacite import from_dict
from congregate.helpers.mdbc import mongo_connection
from congregate.migration.meta.api_models.single_project_features import SingleProjectFeatures
    
def create_archive(pid, export_file):
    final_path = f"{export_file.split('.tar.gz')[0]}_artifact.tar.gz"
    with tarfile.TarFile.open(final_path, 'w:gz') as tar:
        __add_file(tar, Path(export_file).name, GzipFile(export_file, 'rb'))
        __add_file(tar, "project_features.json", __get_project_features(pid))
    return final_path

@mongo_connection
def delete_project_features(pid, mongo=None):
    mongo.db['project_features'].delete_one({'id': pid})

@mongo_connection
def __get_project_features(pid, mongo=None):
    features = mongo.safe_find_one('project_features', query={"id": pid})
    return BytesIO(
        bytes(dumps(
            from_dict(data_class=SingleProjectFeatures, data=features).to_dict()
        ), encoding='utf-8')
    )

def __add_file(tar, path, data):
    new_file = tarfile.TarInfo(path)
    data.seek(0, os.SEEK_END)
    new_file.size = data.tell()
    data.seek(0)
    new_file.mtime = time()
    return tar.addfile(tarinfo=new_file, fileobj=data)

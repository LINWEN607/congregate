import tarfile
import os
from time import time
from json import dumps, load
from io import BytesIO
from pathlib import Path
from dacite import from_dict
from congregate.helpers.configuration_validator import Config
from congregate.helpers.mdbc import mongo_connection
from congregate.migration.meta.api_models.single_project_features import SingleProjectFeatures
    
def create_archive(pid, export_file):
    final_path = f"{export_file.split('.tar.gz')[0]}_artifact.tar.gz"
    with tarfile.TarFile.open(final_path, 'w:gz') as tar:
        __add_file(tar, Path(export_file).name, __read_targz(export_file))
        __add_file(tar, "project_features.json", __get_project_features(pid))
    return final_path

def extract_archive(import_file):
    # open tar for extraction
    project_details = {}
    project_export_filename = ''
    with tarfile.TarFile.open(import_file, 'r:gz') as tar:
        for tf in tar.getmembers():
            if tf.name == "project_features.json":
                # load project features into mongo
                features = load((tar.extractfile(tf)))
                project_details = features.get('project_details')
                load_project_features(features)
            elif ''.join(Path(tf.name).suffixes) == '.tar.gz':
                # download project export
                project_export_filename = tf.name
                export_download_path = os.path.join(Config().filesystem_path, 'downloads', tf.name)
                with open(export_download_path, 'wb') as export_tar:
                    export_tar.write(tar.extractfile(tf).read())
    
    return project_details, project_export_filename

def delete_project_export(filename):
    full_path = os.path.join(Config().filesystem_path, 'downloads', filename)
    if ''.join(Path(full_path).suffixes) == '.tar.gz' and os.path.exists(full_path):
        os.remove(full_path)
        return True
    return False

@mongo_connection
def load_project_features(data, mongo=None):
    mongo.insert_data('project_features', data)

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

def __read_targz(filepath):
    with open(filepath, 'rb') as f:
        return BytesIO(f.read())

def __add_file(tar, path, data):
    new_file = tarfile.TarInfo(path)
    data.seek(0, os.SEEK_END)
    new_file.size = data.tell()
    data.seek(0)
    new_file.mtime = time()
    return tar.addfile(tarinfo=new_file, fileobj=data)

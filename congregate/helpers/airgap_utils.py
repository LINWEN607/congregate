import tarfile
import os
from json import dumps
from io import BytesIO
from gzip import GzipFile
from pathlib import Path
from dacite import from_dict
from congregate.helpers.mdbc import MongoConnector
from congregate.migration.meta.api_models.single_project_features import SingleProjectFeatures
    
def create_archive(pid, export_file):
    with tarfile.TarFile.open(f"{export_file}_artifact.tar", 'w:gz') as tar:
        add_file(tar, Path(export_file).name, GzipFile(export_file, 'rb'))
        add_file(tar, "project_features.json", get_project_features(pid))

def get_project_features(pid):
    mongo = MongoConnector()
    features = mongo.safe_find_one('project_features', query={"id": pid})
    return BytesIO(
        bytes(dumps(
            from_dict(data_class=SingleProjectFeatures, data=features).to_dict()
        ), encoding='utf-8')
    )

def add_file(tar, path, data):
    new_file = tarfile.TarInfo(path)
    data.seek(0, os.SEEK_END)
    new_file.size = data.tell()
    data.seek(0)
    return tar.addfile(tarinfo=new_file, fileobj=data)


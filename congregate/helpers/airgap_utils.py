import tarfile
import os
from json import dumps
from io import StringIO
from pathlib import Path
from dacite import from_dict
from congregate.helpers.mdbc import MongoConnector
from congregate.migration.meta.api_models.single_project_features import SingleProjectFeatures
    
def create_archive(pid, export_file):
    with tarfile.TarFile.open(f"{export_file}_artifact.tar", 'w') as tar:
        add_file(tar, Path(export_file).name, open(export_file))
        # add_file(tar, "project_features.json", get_project_features(pid))

def get_project_features(pid):
    mongo = MongoConnector()
    features = mongo.safe_find_one('project_features', query={"id": pid})
    return StringIO(
        dumps(
            from_dict(data_class=SingleProjectFeatures, data=features).to_dict()
        )
    )

# TODO: Fix this function to handle any file type
def add_file(tar, path, data):
    print(path)
    new_file = tarfile.TarInfo(path)
    # new_file = tarfile.TarFile.gettarinfo(path, fileobj=data)
    data.seek(0, os.SEEK_END)
    new_file.size = data.tell()
    data.seek(0)
    return tar.addfile(tarinfo=new_file, fileobj=data)
    # return tar.addfile(tarfile.TarInfo(path), data)


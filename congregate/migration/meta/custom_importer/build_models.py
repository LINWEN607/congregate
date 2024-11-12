import os
from gitlab_ps_utils.json_utils import read_json_file_into_object, json_pretty

def to_camel_case(snake_str):
    return "".join(x.capitalize() for x in snake_str.lower().split("_"))

models = read_json_file_into_object('congregate/migration/meta/custom_importer/models.json')

for model, fields in models.items():
    if os.path.exists(f"congregate/migration/meta/custom_importer/data_models/{model.replace('.ndjson', '')}.py"):
        continue
    else:
        with open(f"congregate/migration/meta/custom_importer/data_models/{model.replace('.ndjson', '')}.py", "w") as f:
            f.write("""
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none
                    
'''
%s             
'''

@dataclass
class %s:
    pass
                    """ % (json_pretty(fields), to_camel_case(model.replace('.ndjson', ''))))
from dataclasses import dataclass
from congregate.helpers.utils import is_valid_url

@dataclass
class AirgapImportPayload():
    host: str
    token: str
    gid: int

    def __post_init__(self):
        '''
            Validation checks
        '''
        if not isinstance(self.host, str):
            raise TypeError('Host should be of type str')

        if not is_valid_url(self.host):
            raise ValueError(f'Provided host [{self.host}] is not a valid URL')


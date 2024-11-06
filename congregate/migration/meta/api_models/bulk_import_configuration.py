from dataclasses import dataclass


@dataclass
class BulkImportConfiguration:
    url: str
    access_token: str

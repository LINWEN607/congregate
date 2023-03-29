from dataclasses import dataclass

@dataclass
class ExternalCiSourceLookup():
    source: str
    module: str
    class_name: str
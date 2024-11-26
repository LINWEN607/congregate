from typing import Optional
from dataclasses import dataclass, asdict
from gitlab_ps_utils.dict_utils import strip_none
                    
@dataclass
class SecuritySetting:
    '''
        Dataclass for any security settings of a project

        This dataclass is fairly GitLab-specific so this may not be applicable to your use case
    '''
    
    created_at: Optional[str] = None
    project_id: Optional[int] = None
    updated_at: Optional[str] = None

    def to_dict(self):
        return strip_none(asdict(self))

                    
import yaml
from congregate.helpers.base_class import BaseClass

class JobTemplateGenerator(BaseClass):
    def __init__(self):
        super(JobTemplateGenerator, self).__init__()

    def load_template_to_object(self, template_string):
        return yaml.load(template_string, Loader=yaml.FullLoader)

    def to_string(self, yaml_object):
        return yaml.dump(yaml_object, sort_keys=False)

    def generate_plain_html_template(self):

        template = self.load_template_to_object("""
            image: alpine:latest
            
            before_script:
                - apk add rsync
                - mkdir public
                - rsync -aP --exclude=public ./* public/

            pages:
                stage: deploy
                script:
                    - echo 'Nothing to do...'
                artifacts:
                    paths:
                        - public
                only:
                    - gh-pages
        """) 
        return self.to_string(template)

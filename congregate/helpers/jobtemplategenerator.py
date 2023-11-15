import yaml

from congregate.helpers.base_class import BaseClass

class JobTemplateGenerator(BaseClass):
    def __init__(self):
        super().__init__()

    def to_string(self, yaml_object):
        return yaml.dump(yaml_object, sort_keys=False)

    def generate_plain_html_template(self):

        template = yaml.safe_load("""
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

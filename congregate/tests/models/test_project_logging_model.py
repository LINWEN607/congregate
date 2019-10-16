import unittest
from congregate.models.project_logging_model import ProjectLoggingModel


class ProjectLoggingModelTests(unittest.TestCase):
    def setUp(self):
        self.user_model = ProjectLoggingModel()

    def test_proper_fields(self):
        project = {
            "id": 123,
            "name": "some project name",
            "name_with_namespace": "some namespace/some project name"
        }
        return_project_model = self.user_model.get_logging_model(project)
        self.assertDictEqual(project, return_project_model)

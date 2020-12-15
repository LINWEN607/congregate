import unittest
import pytest
from mock import patch, PropertyMock, MagicMock

from congregate.migration.gitlab.clusters import ClustersClient
from congregate.tests.mockapi.gitlab.clusters import MockClustersApi
from congregate.tests.mockapi.gitlab.projects import MockProjectsApi
from congregate.migration.gitlab.projects import ProjectsClient
from congregate.migration.gitlab.api.projects import ProjectsApi


@pytest.mark.unit_test
class ClustersTests(unittest.TestCase):
    def setUp(self):
        self.clusters = ClustersClient()
        self.mock_clusters = MockClustersApi()
        self.mock_projects = MockProjectsApi()

    def test_create_data(self):
        actual = self.clusters.create_data(
            self.mock_clusters.get_cluster(), {}, "Project")
        expected = {
            "name": "cluster-1",
            "domain": "",
            "enabled": False,
            "managed": True,
            "environment_scope": "development",
            "platform_kubernetes_attributes": {
                "api_url": "https://36.111.51.20",
                "token": 6,
                "ca_cert": "-----BEGIN CERTIFICATE-----\nMIIFDjCCAvYCCQDoZqaTnuVIMzANBgkqhkiG9w0BAQsFADBJMQswCQYDVQQGEwJO\nTDELMAkGA1UECAwCU0gxDzANBgNVBAoMBkdpdExhYjEcMBoGCSqGSIb3DQEJARYN\ndGVzdEB0ZXN0LmNvbTAeFw0yMDEwMzAxNzEzMjNaFw0yMTEwMzAxNzEzMjNaMEkx\nCzAJBgNVBAYTAk5MMQswCQYDVQQIDAJTSDEPMA0GA1UECgwGR2l0TGFiMRwwGgYJ\nKoZIhvcNAQkBFg10ZXN0QHRlc3QuY29tMIICIjANBgkqhkiG9w0BAQEFAAOCAg8A\nMIICCgKCAgEAxYESkMcdZM0/ZwyKC83+1uqdROkk2T4AaH0dWtWRvG3X+nO3pUeS\nzCJ5fgOvdtelJAxEmUUCPlD+BApwjJDE6Tl/qNNv44uHM7QAGigXbD4urBzRFzQh\nsZ9mEseaUfLH1QAb6vk/LdgxDkbeaovTUeMafvE467OWTO4iLaApDZTk6gdsO2gi\nQkPaAqf1XhKFowWQrO4GnZVbN66/ja8ZSOXi8wWzJKTwN5ZQR9oCPbetIDBD6KK6\nkKom7ht2zLcxMx/g0bodnSaResMXbPTYKB+Lou4ja4lSRfUGyGa6x1GSQsIcyr12\nbm4xcQylEQEsy9XgCJGsmXfJ8PnEKp2Fu4HwhTsE3dXIeE/x+OAOiDUoc6BT/LDW\nqWchExV/jUkHmPlii3dJ/NXsuCA/5RBga3ES9pEI/+HzYvXhiUBFaJEOhiU887uJ\nk9mGB2uJD/No7RtA579oTOHMLsplNmH7i3lAzKGtL7tMmRmvFa/BCvekpr0FJr17\nr7dU+T/8JtJ5hg0TUOgOTBL57X8E6SvXJ3ZdV0Ml5BpZCtpZbD7Xu7xBXX1jdlR+\nKyN2y8yq9kv86eq0SdSQ3VJ6sXd8RLiSzdtL85QPVC5NyBW5QfbIAC81I0lBBpgc\nLKISJi8UM0EdgmSGFK9JwO+AQqyVi7WMyMo1vW1B01hWWft5bhyW/MkCAwEAATAN\nBgkqhkiG9w0BAQsFAAOCAgEAEUlKdRDNsXpxTJrOhb2fSiylm4Cm/jsmSRrpK53Q\n73rpMzf0xy3C6pSjQGR4d7GP/3bLeYiJLHQma+oYorKv5pgyoInwZkYArcLiqfLu\npapI9NIYVwrI3QO60p0kwc+Tmj0m2sFEbH9Oj8qCu6DxOxaZ1llmzq0zS/AdzyZ0\nw0jEn391y9aYYWiOUzNBLo95CT/DZSrIDXKigsQn5sBXnTF2xtMyV3BSoz/hv5rX\njTjCcCFajzgvxl0z3zsjlDWV7t5kWbTLMxALlkpKjMPE0eSsZdeBQTAC51VBT3xc\nbDefR0snQctYdlrUxEIx9nC6QVecjgjKHWzG8SgiuItMvgZHM40gdPDUaAml6svg\n/1e0wxaJnmndT9acwSCFCQswlgQmso8yh4HILhO9ZaC9G5d+nr2mPs68gn69L/Mi\nEzMqwG8hZ860z+KWQs/S2RufzKOfwIy0/SXTq5f6WrxKTln46CMjHSueaenoMr1Q\n8q/koh/zx5f8HDAhaieQM7LUkTVoZTbjof+m82aveqxXgFlEITA3ciVqUrOAaWZb\n8U48lwlB/xOtEXrgL7sMF2bwk5AeNtGjZG7lpBhiHFP3NGj+fs97UItjV73NqulQ\nrSYVvsu9fWIyWx0Z2Izi10wq9V0R3uAwbAthLB3JK/iNC/0mK5+kIWxn8QafZlwK\nkpM=\n-----END CERTIFICATE-----",
                "namespace": "cluster-1-namespace",
                "authorization_type": "rbac"
            }
        }
        self.assertEqual(actual, expected)

    @patch.object(ProjectsApi, "get_project")
    @patch.object(ProjectsClient, "find_project_by_path")
    @patch('congregate.helpers.conf.Config.source_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.source_token', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.destination_host', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.destination_token', new_callable=PropertyMock)
    @patch('congregate.helpers.conf.Config.src_parent_id', new_callable=PropertyMock)
    @patch('congregate.helpers.configuration_validator.ConfigurationValidator.dstn_parent_id', new_callable=PropertyMock)
    def test_create_data_with_mp(self, mock_dstn_parent_id, mock_src_parent_id, mock_dstn_token, mock_dstn_host, mock_src_token, mock_src_host, mock_find_project, mock_project):
        mock_src_parent_id.return_value = None
        mock_dstn_parent_id.return_value = None
        mock_dstn_token.return_value = "token"
        mock_dstn_host.return_value = "https://gitlab.dstn.com"
        mock_src_token.return_value = "token"
        mock_src_host.return_value = "https://gitlab.src.com"
        mock_find_project.return_value = 42
        mock_project = MagicMock()
        type(mock_project).status_code = PropertyMock(return_value=200)
        mock_project.json.return_value = self.mock_projects.get_project()

        actual = self.clusters.create_data(
            self.mock_clusters.get_cluster_with_mp(), {}, "Project")
        expected = {
            "name": "cluster-1",
            "domain": "",
            "enabled": True,
            "managed": True,
            "management_project_id": 42,
            "environment_scope": "development",
            "platform_kubernetes_attributes": {
                "api_url": "https://36.111.51.20",
                "token": 6,
                "ca_cert": "-----BEGIN CERTIFICATE-----\nMIIFDjCCAvYCCQDoZqaTnuVIMzANBgkqhkiG9w0BAQsFADBJMQswCQYDVQQGEwJO\nTDELMAkGA1UECAwCU0gxDzANBgNVBAoMBkdpdExhYjEcMBoGCSqGSIb3DQEJARYN\ndGVzdEB0ZXN0LmNvbTAeFw0yMDEwMzAxNzEzMjNaFw0yMTEwMzAxNzEzMjNaMEkx\nCzAJBgNVBAYTAk5MMQswCQYDVQQIDAJTSDEPMA0GA1UECgwGR2l0TGFiMRwwGgYJ\nKoZIhvcNAQkBFg10ZXN0QHRlc3QuY29tMIICIjANBgkqhkiG9w0BAQEFAAOCAg8A\nMIICCgKCAgEAxYESkMcdZM0/ZwyKC83+1uqdROkk2T4AaH0dWtWRvG3X+nO3pUeS\nzCJ5fgOvdtelJAxEmUUCPlD+BApwjJDE6Tl/qNNv44uHM7QAGigXbD4urBzRFzQh\nsZ9mEseaUfLH1QAb6vk/LdgxDkbeaovTUeMafvE467OWTO4iLaApDZTk6gdsO2gi\nQkPaAqf1XhKFowWQrO4GnZVbN66/ja8ZSOXi8wWzJKTwN5ZQR9oCPbetIDBD6KK6\nkKom7ht2zLcxMx/g0bodnSaResMXbPTYKB+Lou4ja4lSRfUGyGa6x1GSQsIcyr12\nbm4xcQylEQEsy9XgCJGsmXfJ8PnEKp2Fu4HwhTsE3dXIeE/x+OAOiDUoc6BT/LDW\nqWchExV/jUkHmPlii3dJ/NXsuCA/5RBga3ES9pEI/+HzYvXhiUBFaJEOhiU887uJ\nk9mGB2uJD/No7RtA579oTOHMLsplNmH7i3lAzKGtL7tMmRmvFa/BCvekpr0FJr17\nr7dU+T/8JtJ5hg0TUOgOTBL57X8E6SvXJ3ZdV0Ml5BpZCtpZbD7Xu7xBXX1jdlR+\nKyN2y8yq9kv86eq0SdSQ3VJ6sXd8RLiSzdtL85QPVC5NyBW5QfbIAC81I0lBBpgc\nLKISJi8UM0EdgmSGFK9JwO+AQqyVi7WMyMo1vW1B01hWWft5bhyW/MkCAwEAATAN\nBgkqhkiG9w0BAQsFAAOCAgEAEUlKdRDNsXpxTJrOhb2fSiylm4Cm/jsmSRrpK53Q\n73rpMzf0xy3C6pSjQGR4d7GP/3bLeYiJLHQma+oYorKv5pgyoInwZkYArcLiqfLu\npapI9NIYVwrI3QO60p0kwc+Tmj0m2sFEbH9Oj8qCu6DxOxaZ1llmzq0zS/AdzyZ0\nw0jEn391y9aYYWiOUzNBLo95CT/DZSrIDXKigsQn5sBXnTF2xtMyV3BSoz/hv5rX\njTjCcCFajzgvxl0z3zsjlDWV7t5kWbTLMxALlkpKjMPE0eSsZdeBQTAC51VBT3xc\nbDefR0snQctYdlrUxEIx9nC6QVecjgjKHWzG8SgiuItMvgZHM40gdPDUaAml6svg\n/1e0wxaJnmndT9acwSCFCQswlgQmso8yh4HILhO9ZaC9G5d+nr2mPs68gn69L/Mi\nEzMqwG8hZ860z+KWQs/S2RufzKOfwIy0/SXTq5f6WrxKTln46CMjHSueaenoMr1Q\n8q/koh/zx5f8HDAhaieQM7LUkTVoZTbjof+m82aveqxXgFlEITA3ciVqUrOAaWZb\n8U48lwlB/xOtEXrgL7sMF2bwk5AeNtGjZG7lpBhiHFP3NGj+fs97UItjV73NqulQ\nrSYVvsu9fWIyWx0Z2Izi10wq9V0R3uAwbAthLB3JK/iNC/0mK5+kIWxn8QafZlwK\nkpM=\n-----END CERTIFICATE-----",
                "namespace": "cluster-1-namespace",
                "authorization_type": "rbac"
            }
        }
        self.assertEqual(actual, expected)

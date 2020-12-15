class MockClustersApi():
    def get_cluster(self):
        return {
            "id": 6,
            "name": "cluster-1",
            "created_at": "2020-11-01T22:42:42.764Z",
            "domain": "",
            "enabled": False,
            "managed": True,
            "provider_type": "user",
            "platform_type": "kubernetes",
            "environment_scope": "development",
            "cluster_type": "project_type",
            "namespace_per_environment": True,
            "user": {
                "id": 60,
                "name": "admin_congregate",
                "username": "admin_congregate",
                "state": "active",
                "avatar_url": "https://secure.gravatar.com/avatar/9628dda760967deae8144112be082600?s=80&d=identicon",
                "web_url": "https://pprokic.tanuki.cloud/admin_congregate"
            },
            "platform_kubernetes": {
                "api_url": "https://36.111.51.20",
                "namespace": "cluster-1-namespace",
                "authorization_type": "rbac",
                "ca_cert": "-----BEGIN CERTIFICATE-----\nMIIFDjCCAvYCCQDoZqaTnuVIMzANBgkqhkiG9w0BAQsFADBJMQswCQYDVQQGEwJO\nTDELMAkGA1UECAwCU0gxDzANBgNVBAoMBkdpdExhYjEcMBoGCSqGSIb3DQEJARYN\ndGVzdEB0ZXN0LmNvbTAeFw0yMDEwMzAxNzEzMjNaFw0yMTEwMzAxNzEzMjNaMEkx\nCzAJBgNVBAYTAk5MMQswCQYDVQQIDAJTSDEPMA0GA1UECgwGR2l0TGFiMRwwGgYJ\nKoZIhvcNAQkBFg10ZXN0QHRlc3QuY29tMIICIjANBgkqhkiG9w0BAQEFAAOCAg8A\nMIICCgKCAgEAxYESkMcdZM0/ZwyKC83+1uqdROkk2T4AaH0dWtWRvG3X+nO3pUeS\nzCJ5fgOvdtelJAxEmUUCPlD+BApwjJDE6Tl/qNNv44uHM7QAGigXbD4urBzRFzQh\nsZ9mEseaUfLH1QAb6vk/LdgxDkbeaovTUeMafvE467OWTO4iLaApDZTk6gdsO2gi\nQkPaAqf1XhKFowWQrO4GnZVbN66/ja8ZSOXi8wWzJKTwN5ZQR9oCPbetIDBD6KK6\nkKom7ht2zLcxMx/g0bodnSaResMXbPTYKB+Lou4ja4lSRfUGyGa6x1GSQsIcyr12\nbm4xcQylEQEsy9XgCJGsmXfJ8PnEKp2Fu4HwhTsE3dXIeE/x+OAOiDUoc6BT/LDW\nqWchExV/jUkHmPlii3dJ/NXsuCA/5RBga3ES9pEI/+HzYvXhiUBFaJEOhiU887uJ\nk9mGB2uJD/No7RtA579oTOHMLsplNmH7i3lAzKGtL7tMmRmvFa/BCvekpr0FJr17\nr7dU+T/8JtJ5hg0TUOgOTBL57X8E6SvXJ3ZdV0Ml5BpZCtpZbD7Xu7xBXX1jdlR+\nKyN2y8yq9kv86eq0SdSQ3VJ6sXd8RLiSzdtL85QPVC5NyBW5QfbIAC81I0lBBpgc\nLKISJi8UM0EdgmSGFK9JwO+AQqyVi7WMyMo1vW1B01hWWft5bhyW/MkCAwEAATAN\nBgkqhkiG9w0BAQsFAAOCAgEAEUlKdRDNsXpxTJrOhb2fSiylm4Cm/jsmSRrpK53Q\n73rpMzf0xy3C6pSjQGR4d7GP/3bLeYiJLHQma+oYorKv5pgyoInwZkYArcLiqfLu\npapI9NIYVwrI3QO60p0kwc+Tmj0m2sFEbH9Oj8qCu6DxOxaZ1llmzq0zS/AdzyZ0\nw0jEn391y9aYYWiOUzNBLo95CT/DZSrIDXKigsQn5sBXnTF2xtMyV3BSoz/hv5rX\njTjCcCFajzgvxl0z3zsjlDWV7t5kWbTLMxALlkpKjMPE0eSsZdeBQTAC51VBT3xc\nbDefR0snQctYdlrUxEIx9nC6QVecjgjKHWzG8SgiuItMvgZHM40gdPDUaAml6svg\n/1e0wxaJnmndT9acwSCFCQswlgQmso8yh4HILhO9ZaC9G5d+nr2mPs68gn69L/Mi\nEzMqwG8hZ860z+KWQs/S2RufzKOfwIy0/SXTq5f6WrxKTln46CMjHSueaenoMr1Q\n8q/koh/zx5f8HDAhaieQM7LUkTVoZTbjof+m82aveqxXgFlEITA3ciVqUrOAaWZb\n8U48lwlB/xOtEXrgL7sMF2bwk5AeNtGjZG7lpBhiHFP3NGj+fs97UItjV73NqulQ\nrSYVvsu9fWIyWx0Z2Izi10wq9V0R3uAwbAthLB3JK/iNC/0mK5+kIWxn8QafZlwK\nkpM=\n-----END CERTIFICATE-----"
            },
            "provider_gcp": None,
            "management_project": None
        }

    def get_cluster_with_mp(self):
        return {
            "id": 6,
            "name": "cluster-1",
            "created_at": "2020-11-01T22:42:42.764Z",
            "domain": "",
            "provider_type": "user",
            "platform_type": "kubernetes",
            "environment_scope": "development",
            "cluster_type": "project_type",
            "namespace_per_environment": True,
            "user": {
                "id": 60,
                "name": "admin_congregate",
                "username": "admin_congregate",
                "state": "active",
                "avatar_url": "https://secure.gravatar.com/avatar/9628dda760967deae8144112be082600?s=80&d=identicon",
                "web_url": "https://pprokic.tanuki.cloud/admin_congregate"
            },
            "platform_kubernetes": {
                "api_url": "https://36.111.51.20",
                "namespace": "cluster-1-namespace",
                "authorization_type": "rbac",
                "ca_cert": "-----BEGIN CERTIFICATE-----\nMIIFDjCCAvYCCQDoZqaTnuVIMzANBgkqhkiG9w0BAQsFADBJMQswCQYDVQQGEwJO\nTDELMAkGA1UECAwCU0gxDzANBgNVBAoMBkdpdExhYjEcMBoGCSqGSIb3DQEJARYN\ndGVzdEB0ZXN0LmNvbTAeFw0yMDEwMzAxNzEzMjNaFw0yMTEwMzAxNzEzMjNaMEkx\nCzAJBgNVBAYTAk5MMQswCQYDVQQIDAJTSDEPMA0GA1UECgwGR2l0TGFiMRwwGgYJ\nKoZIhvcNAQkBFg10ZXN0QHRlc3QuY29tMIICIjANBgkqhkiG9w0BAQEFAAOCAg8A\nMIICCgKCAgEAxYESkMcdZM0/ZwyKC83+1uqdROkk2T4AaH0dWtWRvG3X+nO3pUeS\nzCJ5fgOvdtelJAxEmUUCPlD+BApwjJDE6Tl/qNNv44uHM7QAGigXbD4urBzRFzQh\nsZ9mEseaUfLH1QAb6vk/LdgxDkbeaovTUeMafvE467OWTO4iLaApDZTk6gdsO2gi\nQkPaAqf1XhKFowWQrO4GnZVbN66/ja8ZSOXi8wWzJKTwN5ZQR9oCPbetIDBD6KK6\nkKom7ht2zLcxMx/g0bodnSaResMXbPTYKB+Lou4ja4lSRfUGyGa6x1GSQsIcyr12\nbm4xcQylEQEsy9XgCJGsmXfJ8PnEKp2Fu4HwhTsE3dXIeE/x+OAOiDUoc6BT/LDW\nqWchExV/jUkHmPlii3dJ/NXsuCA/5RBga3ES9pEI/+HzYvXhiUBFaJEOhiU887uJ\nk9mGB2uJD/No7RtA579oTOHMLsplNmH7i3lAzKGtL7tMmRmvFa/BCvekpr0FJr17\nr7dU+T/8JtJ5hg0TUOgOTBL57X8E6SvXJ3ZdV0Ml5BpZCtpZbD7Xu7xBXX1jdlR+\nKyN2y8yq9kv86eq0SdSQ3VJ6sXd8RLiSzdtL85QPVC5NyBW5QfbIAC81I0lBBpgc\nLKISJi8UM0EdgmSGFK9JwO+AQqyVi7WMyMo1vW1B01hWWft5bhyW/MkCAwEAATAN\nBgkqhkiG9w0BAQsFAAOCAgEAEUlKdRDNsXpxTJrOhb2fSiylm4Cm/jsmSRrpK53Q\n73rpMzf0xy3C6pSjQGR4d7GP/3bLeYiJLHQma+oYorKv5pgyoInwZkYArcLiqfLu\npapI9NIYVwrI3QO60p0kwc+Tmj0m2sFEbH9Oj8qCu6DxOxaZ1llmzq0zS/AdzyZ0\nw0jEn391y9aYYWiOUzNBLo95CT/DZSrIDXKigsQn5sBXnTF2xtMyV3BSoz/hv5rX\njTjCcCFajzgvxl0z3zsjlDWV7t5kWbTLMxALlkpKjMPE0eSsZdeBQTAC51VBT3xc\nbDefR0snQctYdlrUxEIx9nC6QVecjgjKHWzG8SgiuItMvgZHM40gdPDUaAml6svg\n/1e0wxaJnmndT9acwSCFCQswlgQmso8yh4HILhO9ZaC9G5d+nr2mPs68gn69L/Mi\nEzMqwG8hZ860z+KWQs/S2RufzKOfwIy0/SXTq5f6WrxKTln46CMjHSueaenoMr1Q\n8q/koh/zx5f8HDAhaieQM7LUkTVoZTbjof+m82aveqxXgFlEITA3ciVqUrOAaWZb\n8U48lwlB/xOtEXrgL7sMF2bwk5AeNtGjZG7lpBhiHFP3NGj+fs97UItjV73NqulQ\nrSYVvsu9fWIyWx0Z2Izi10wq9V0R3uAwbAthLB3JK/iNC/0mK5+kIWxn8QafZlwK\nkpM=\n-----END CERTIFICATE-----"
            },
            "provider_gcp": None,
            "management_project": {
                "id": 42,
                "description": "",
                "name": "Test Project",
                "name_with_namespace": "Test / Test Project",
                "path": "test-project",
                "path_with_namespace": "test/test-project",
                "created_at": "2020-02-28T13:07:44.563Z"
            }
        }

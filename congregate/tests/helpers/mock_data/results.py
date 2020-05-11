class MockProjectResults():
    def get_completely_successful_results(self):
        return [
            {
                "group-path/subgroup-path/projectA": {
                    "container_registry": True,
                    "push_rules": True,
                    "variables": True,
                    "deploy_keys": True,
                    "environments": True,
                    "project_level_mr_approvals": True,
                    "project_hooks": True,
                    "id": 1,
                    "shared_with_groups": True
                },
            }, {
                "group-path/subgroup-path/projectB": {
                    "container_registry": True,
                    "push_rules": True,
                    "variables": True,
                    "deploy_keys": True,
                    "environments": True,
                    "project_level_mr_approvals": True,
                    "project_hooks": True,
                    "id": 2,
                    "shared_with_groups": True
                },
            }, {
                "group-path/subgroup-path/projectC": {
                    "container_registry": True,
                    "push_rules": True,
                    "variables": True,
                    "deploy_keys": True,
                    "environments": True,
                    "project_level_mr_approvals": True,
                    "project_hooks": True,
                    "id": 3,
                    "shared_with_groups": True
                },
            }, {
                "group-path/subgroup-path/projectD": {
                    "container_registry": True,
                    "push_rules": True,
                    "variables": True,
                    "deploy_keys": True,
                    "environments": True,
                    "project_level_mr_approvals": True,
                    "project_hooks": True,
                    "id": 4,
                    "shared_with_groups": True
                },
            }, {
                "group-path/subgroup-path/projectE": {
                    "container_registry": True,
                    "push_rules": True,
                    "variables": True,
                    "deploy_keys": True,
                    "environments": True,
                    "project_level_mr_approvals": True,
                    "project_hooks": True,
                    "id": 5,
                    "shared_with_groups": True
                }
            }
        ]

    def get_completely_failed_results(self):
        return [
            {"group-path/subgroup-path/projectA": False},
            {"group-path/subgroup-path/projectB": False},
            {"group-path/subgroup-path/projectC": False},
            {"group-path/subgroup-path/projectD": False},
            {"group-path/subgroup-path/projectE": False}
        ]

    def get_partially_successful_results(self):
        return [
            {
                "group-path/subgroup-path/projectA": {
                    "container_registry": True,
                    "push_rules": True,
                    "variables": True,
                    "deploy_keys": True,
                    "environments": True,
                    "project_level_mr_approvals": True,
                    "project_hooks": True,
                    "id": 1,
                    "shared_with_groups": True
                },
            }, {
                "group-path/subgroup-path/projectB": {
                    "container_registry": True,
                    "push_rules": True,
                    "variables": True,
                    "deploy_keys": True,
                    "environments": True,
                    "project_level_mr_approvals": True,
                    "project_hooks": True,
                    "id": 2,
                    "shared_with_groups": True
                },
            }, {
                "group-path/subgroup-path/projectC": {
                    "container_registry": True,
                    "push_rules": True,
                    "variables": True,
                    "deploy_keys": True,
                    "environments": True,
                    "project_level_mr_approvals": True,
                    "project_hooks": True,
                    "id": 3,
                    "shared_with_groups": True
                },
            }, {
                "group-path/subgroup-path/projectD": False,
            }, {
                "group-path/subgroup-path/projectE": False
            }
        ]

    def get_successful_results_subset(self):
        return [
            {
                "group-path/subgroup-path/projectD": {
                    "container_registry": True,
                    "push_rules": True,
                    "variables": True,
                    "deploy_keys": True,
                    "environments": True,
                    "project_level_mr_approvals": True,
                    "project_hooks": True,
                    "id": 4,
                    "shared_with_groups": True
                },
            }, {
                "group-path/subgroup-path/projectE": {
                    "container_registry": True,
                    "push_rules": True,
                    "variables": True,
                    "deploy_keys": True,
                    "environments": True,
                    "project_level_mr_approvals": True,
                    "project_hooks": True,
                    "id": 5,
                    "shared_with_groups": True
                }
            }
        ]

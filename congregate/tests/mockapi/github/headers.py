class MockHeaders():
    def get_linked_headers(self):
        return {
            'X-XSS-Protection': '1; mode=block',
            'Content-Security-Policy': "default-src 'none'",
            'Access-Control-Expose-Headers': 'ETag, Link, Location, Retry-After, X-GitHub-OTP, X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset, X-OAuth-Scopes, X-Accepted-OAuth-Scopes, X-Poll-Interval, X-GitHub-Media-Type, Deprecation, Sunset',
            'X-GitHub-Enterprise-Version': '2.21.2',
            'Access-Control-Allow-Origin': '*',
            'X-Frame-Options': 'deny',
            'Status': '200 OK',
            'X-GitHub-Request-Id': 'd9eb4f1f-9806-4fee-95d8-4ed0630998a0',
            'Link': '<https://github.gitlab-proserv.net/api/v3/organizations?since=12>; rel="next", <https://github.gitlab-proserv.net/api/v3/organizations{?since}>; rel="first"',
            'Date': 'Fri, 31 Jul 2020 23:29:56 GMT',
            'X-Runtime-Rack': '0.031050',
            'transfer-encoding': 'chunked',
            'Strict-Transport-Security': 'max-age=31536000; includeSubdomains',
            'Server': 'GitHub.com',
            'X-OAuth-Scopes': 'admin:enterprise, admin:gpg_key, admin:org, admin:org_hook, admin:pre_receive_hook, admin:public_key, admin:repo_hook, delete_repo, gist, notifications, repo, site_admin, user, write:discussion',
            # 'X-GitHub-Media-Type': 'github.v3; format=json', 'X-Content-Type-Options': 'nosniff', 'Content-Encoding': 'gzip', 'Vary': 'Accept, Authorization, Cookie, X-GitHub-OTP',
            'ETag': 'W/"0c7766e460a97d855208f996656be494"',
            'Cache-Control': 'private, max-age=60, s-maxage=60',
            'Referrer-Policy': 'origin-when-cross-origin, strict-origin-when-cross-origin',
            'Content-Type': 'application/json; charset=utf-8',
            'X-Accepted-OAuth-Scopes': ''
        }

    def get_page_2_linked_headers(self):
        return {
            'X-XSS-Protection': '1; mode=block',
            'Content-Security-Policy': "default-src 'none'",
            'Access-Control-Expose-Headers': 'ETag, Link, Location, Retry-After, X-GitHub-OTP, X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset, X-OAuth-Scopes, X-Accepted-OAuth-Scopes, X-Poll-Interval, X-GitHub-Media-Type, Deprecation, Sunset',
            'X-GitHub-Enterprise-Version': '2.21.2',
            'Access-Control-Allow-Origin': '*',
            'X-Frame-Options': 'deny',
            'Status': '200 OK',
            'X-GitHub-Request-Id': 'd9eb4f1f-9806-4fee-95d8-4ed0630998a0',
            'Link': '<https://github.gitlab-proserv.net/api/v3/organizations?since=24>; rel="next", <https://github.gitlab-proserv.net/api/v3/organizations{?since}>; rel="first"',
            'Date': 'Fri, 31 Jul 2020 23:29:56 GMT',
            'X-Runtime-Rack': '0.031050',
            'transfer-encoding': 'chunked',
            'Strict-Transport-Security': 'max-age=31536000; includeSubdomains',
            'Server': 'GitHub.com',
            'X-OAuth-Scopes': 'admin:enterprise, admin:gpg_key, admin:org, admin:org_hook, admin:pre_receive_hook, admin:public_key, admin:repo_hook, delete_repo, gist, notifications, repo, site_admin, user, write:discussion',
            # 'X-GitHub-Media-Type': 'github.v3; format=json', 'X-Content-Type-Options': 'nosniff', 'Content-Encoding': 'gzip', 'Vary': 'Accept, Authorization, Cookie, X-GitHub-OTP',
            'ETag': 'W/"0c7766e460a97d855208f996656be494"',
            'Cache-Control': 'private, max-age=60, s-maxage=60',
            'Referrer-Policy': 'origin-when-cross-origin, strict-origin-when-cross-origin',
            'Content-Type': 'application/json; charset=utf-8',
            'X-Accepted-OAuth-Scopes': ''
        }

    def get_linkless_headers(self):
        return {
            'X-XSS-Protection': '1; mode=block',
            'Content-Security-Policy': "default-src 'none'",
            'Access-Control-Expose-Headers': 'ETag, Link, Location, Retry-After, X-GitHub-OTP, X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset, X-OAuth-Scopes, X-Accepted-OAuth-Scopes, X-Poll-Interval, X-GitHub-Media-Type, Deprecation, Sunset',
            'X-GitHub-Enterprise-Version': '2.21.2',
            'Access-Control-Allow-Origin': '*',
            'X-Frame-Options': 'deny',
            'Status': '200 OK',
            'X-GitHub-Request-Id': 'd9eb4f1f-9806-4fee-95d8-4ed0630998a0',
            'Date': 'Fri, 31 Jul 2020 23:29:56 GMT',
            'X-Runtime-Rack': '0.031050',
            'transfer-encoding': 'chunked',
            'Strict-Transport-Security': 'max-age=31536000; includeSubdomains',
            'Server': 'GitHub.com',
            'X-OAuth-Scopes': 'admin:enterprise, admin:gpg_key, admin:org, admin:org_hook, admin:pre_receive_hook, admin:public_key, admin:repo_hook, delete_repo, gist, notifications, repo, site_admin, user, write:discussion',
            # 'X-GitHub-Media-Type': 'github.v3; format=json', 'X-Content-Type-Options': 'nosniff', 'Content-Encoding': 'gzip', 'Vary': 'Accept, Authorization, Cookie, X-GitHub-OTP',
            'ETag': 'W/"0c7766e460a97d855208f996656be494"',
            'Cache-Control': 'private, max-age=60, s-maxage=60',
            'Referrer-Policy': 'origin-when-cross-origin, strict-origin-when-cross-origin',
            'Content-Type': 'application/json; charset=utf-8',
            'X-Accepted-OAuth-Scopes': ''
        }

    def get_data(self):
        return [
            {
                "login": "org1",
                "id": 8,
                "node_id": "MDEyOk9yZ2FuaXphdGlvbjg=",
                "url": "https://github.gitlab-proserv.net/api/v3/orgs/org1",
                "repos_url": "https://github.gitlab-proserv.net/api/v3/orgs/org1/repos",
                "events_url": "https://github.gitlab-proserv.net/api/v3/orgs/org1/events",
                "hooks_url": "https://github.gitlab-proserv.net/api/v3/orgs/org1/hooks",
                "issues_url": "https://github.gitlab-proserv.net/api/v3/orgs/org1/issues",
                "members_url": "https://github.gitlab-proserv.net/api/v3/orgs/org1/members{/member}",
                "public_members_url": "https://github.gitlab-proserv.net/api/v3/orgs/org1/public_members{/member}",
                "avatar_url": "https://github.gitlab-proserv.net/avatars/u/8?",
                "description": None
            },
            {
                "login": "org2",
                "id": 9,
                "node_id": "MDEyOk9yZ2FuaXphdGlvbjg=",
                "url": "https://github.gitlab-proserv.net/api/v3/orgs/org2",
                "repos_url": "https://github.gitlab-proserv.net/api/v3/orgs/org2/repos",
                "events_url": "https://github.gitlab-proserv.net/api/v3/orgs/org2/events",
                "hooks_url": "https://github.gitlab-proserv.net/api/v3/orgs/org2/hooks",
                "issues_url": "https://github.gitlab-proserv.net/api/v3/orgs/org2/issues",
                "members_url": "https://github.gitlab-proserv.net/api/v3/orgs/org2/members{/member}",
                "public_members_url": "https://github.gitlab-proserv.net/api/v3/orgs/org2/public_members{/member}",
                "avatar_url": "https://github.gitlab-proserv.net/avatars/u/8?",
                "description": None
            },
            {
                "login": "org3",
                "id": 10,
                "node_id": "MDEyOk9yZ2FuaXphdGlvbjg=",
                "url": "https://github.gitlab-proserv.net/api/v3/orgs/org3",
                "repos_url": "https://github.gitlab-proserv.net/api/v3/orgs/org3/repos",
                "events_url": "https://github.gitlab-proserv.net/api/v3/orgs/org3/events",
                "hooks_url": "https://github.gitlab-proserv.net/api/v3/orgs/org3/hooks",
                "issues_url": "https://github.gitlab-proserv.net/api/v3/orgs/org3/issues",
                "members_url": "https://github.gitlab-proserv.net/api/v3/orgs/org3/members{/member}",
                "public_members_url": "https://github.gitlab-proserv.net/api/v3/orgs/org3/public_members{/member}",
                "avatar_url": "https://github.gitlab-proserv.net/avatars/u/8?",
                "description": None
            }
        ]

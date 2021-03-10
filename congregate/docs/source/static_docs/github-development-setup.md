# GitHub Development in Congregate

## Installing GHE Server on Azure

The current test instance is installed on Azure by following the [official docs](https://docs.github.com/en/enterprise/2.21/admin/installation/installing-github-enterprise-server-on-azure).

### Site admin dashboard

Once GitHub Enterprise Server is up and running, you can configure the appliance to suit your needs.

Use the site admin dashboard to configure, among others:

- License info
- Management console (Authentication, SSL, etc.)
- Repositories (archiving/unarchiving, LFS, etc.)
- Users (dormant/suspended, site admins, etc.)

#### Managing your GitHub Enterprise license

The installation comes with a 45-day trial license with no seat restrictions.

Once that period expires a license is needed to unlock the application via web browser and Git. You will still be able to back up all of your data using `ghe-*` command line utilities.

For more details on how to purchase/renew your license see [here](https://docs.github.com/en/enterprise/2.21/admin/overview/managing-your-github-enterprise-license).

#### Configuring your enterprise

To make sure you are authenticated, as a site admin or regular user, access the management console. For details see [here](https://docs.github.com/en/enterprise/2.21/admin/configuration/accessing-the-management-console).

For configurating the rate limits see [here](https://docs.github.com/en/enterprise/2.21/admin/configuration/configuring-rate-limits) for more details.

#### Users and access permissions

GitHub Enterprise Server provides 3 types of accounts:

- **Admin** - May and should have a small set of trusted administrators with access to underlying OS, FS and DB.
- **User** - Full access to their own data and any data that other users or organizations explicitly grant them.
- **Site admin** - Users with access to high-level web application and appliance settings, user and organization account settings and repository data.

For more datils see [here](https://docs.github.com/en/enterprise/2.21/user/github/getting-started-with-github/access-permissions-on-github).

#### Authentication

GitHub Enterprise Server provides 4 authentication methods:

- **SSH Public key** - Git repository and administrative shell access.
- **Username and password** - HTTP web application access and session management, with optional 2FA.
- **External LDAP, SAML, or CAS authentication** - Using an LDAP service, SAML Identity Provider (IdP), or other compatible service provides access to the web application.
- **OAuth and Personal Access Token (PAT)** - Git repository and API access for external clients and services.

For more details on creating PATs, the authentication method relevant to Congregate migrations, see [here](https://docs.github.com/en/enterprise/2.21/user/github/authenticating-to-github/creating-a-personal-access-token).

## Accessing the instance via API

GitHub currently supports 2 web service APIs:

- GraphQL (v4)
- REST (v3)

Both require an OAuth token with the right scopes for authentication. Althought REST also allows authentication via username and password it is not encouraged and will be deprecated. See [here](https://docs.github.com/en/enterprise/2.21/user/rest/overview/other-authentication-methods) for more details.

### GraphQL API overview

As GraphQL is currently not the primary API used for migrations the overview is limited to visiting the [official docs](https://docs.github.com/en/enterprise/2.21/user/graphql/overview) for more details.

### REST API overview

By default all (v3) requests are encouraged to explicitly use the following header:

```json
Accept: application/vnd.github.v3+json
```

For OAuth authentication add the following header to your request:

```json
Authorization: token OAUTH-TOKEN
```

For **Pagination** see [here](https://docs.github.com/en/enterprise/2.21/user/rest/overview/resources-in-the-rest-api#pagination) for more details.

For **Rate limiting** see [here](https://docs.github.com/en/enterprise/2.21/user/rest/overview/resources-in-the-rest-api#rate-limiting) for more details.

For consuming different **Media types**, besides JSON, see [here](https://docs.github.com/en/enterprise/2.21/user/rest/overview/media-types) for more details.

For available resources see [here](https://docs.github.com/en/enterprise/2.21/user/rest/reference) for more details. Your main focus should be on:

- Organizations
- Projects
- Repositories
- Teams
- Users

Certain API resources require a custom media type in the `Accept` header for your requests. These are called **API previews**.

A good example are **Projects**, which require the following `Accept` header:

```json
Accept: application/vnd.github.inertia-preview+json
```

See [here](https://docs.github.com/en/enterprise/2.21/user/rest/overview/api-previews) for more details.

#### Resources with limited access

Certain resources are only avaialable to request with the authenticated user's PAT, among others.

- Private repositories - `/users/{username}/repos`
- Repository collaborators - `/repos/{owner}/{repo}/collaborators`
- Other `*/{owner}/*` resources

Others only exist on an organization i.e. team level, among others:

- Repository teams - `/repos/{owner}/{repo}/teams`

## Seeding the e2e test source instance

Once we have the GHE Server source instance up and running it's time to seed it with some dummy data, mainly GitHub:

- Users
- Repositories
- Organizations
- Teams

We have that procedure automated by running script `<command>`.

<!-- TODO: Add more details. -->

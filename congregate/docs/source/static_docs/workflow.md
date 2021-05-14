# Migration Workflow

## Legend

:white_check_mark: = supported

:heavy_minus_sign: = not yet supported / in development

:x: = not supported

## Pre-migration steps

### Pre-requisites and considerations

* The GitLab Project export / import API versions need to match between instances. [This documentation](https://docs.gitlab.com/ee/user/project/settings/import_export.html) shows which versions of the API exist in each version of GitLab.
* The GitLab Group export / import API versions need to match between instances and be at least on **12.8**, but preferebly **13.3**.
* GitLab admin Access Token with `api` scope (read and write, until more granular API scopes are available) for both source and destination instance
* Environment (VM, k8s, etc.) for running Congregate Docker image
  * Minimum environment requirements:
    * 4 CPU
    * 8 Gb RAM
    * 20 Gb of disk space (Docker mount volume)
  * Docker installed in order to pull the Congregate image from `registry.gitlab.com` and run a container
* GitLab source instance numbers and sizes:
  * Users (active, blocked, deactivated (:heavy_minus_sign:), external)
  * Groups (top-level groups)
  * Projects (LFS, Container Registry Images) - may require breaking up into migration waves

```eval_rst
.. mermaid::

    graph TD
        A(Source considerations) --> |Users| B{Type}
        B --> C(Blocked)
        B --> D(Deactivated)
        B --> E(External)
        A --> |Groups| F(Top-level)
        A --> |Projects| G{Features}
        G --> H(LFS)
        G --> I(Container Registry Images)
```

* GitLab destination instance considerations:
  * Enable Shared Runners (Default: `True`)?
  * Append project suffix to duplicate project, with the same name (Default: `False`)?
  * Migrate to parent group i.e. new top-level group (parent group ID in **Group -> Settings -> General**)?
  * Append username suffix to avoid username collision (duplicate usernames for users NOT found by email)?
  * Keep blocked / deactivated (:heavy_minus_sign:) users (Default: `False`)?
  * Send user password reset link (via email) upon their creation (Default: `True`)?
  * Set newly created user password to a random value (Default: `False`)?

```eval_rst
.. mermaid::

    graph TD
        A(Destination considerations) --> |True| B(Enable shared runners)
        A --> |False| C(Append project suffix)
        A --> |?| D(Migrate to parent group)
        A --> |?| E(Append username suffix)
        A --> |False| F(Keep inactive users)
        A --> |True| G(Reset pwd)
        A --> |False| H(Force random pwd)
```

* Export storage considerations - for storing group and project archives (exports), container registry images, logs
  * Local filesystem :white_check_mark:
  * AWS S3 bucket
    * Projects :white_check_mark:
    * Groups :heavy_minus_sign:
  * Hybrid (Filesystem-AWS) :heavy_minus_sign:

```eval_rst
.. mermaid::

    graph TD
        A(Export storage) --> |Groups & Projects| B(Filesystem)
        A --> |Projects| C(AWS S3)
```

### Timing and Planning

* Users:
  * Disable email notifications (request destination instance Admin or GitLab Support)
  * Broadcast message on source instance
* Groups - small in size, only the Group’s tree structure is exported / imported
* Projects - due to cut-over time and size constraints we may break them down into separate waves of even size and grouped by parent group

## Migration Steps

### Dry-run

```eval_rst
.. mermaid::

    graph TD
        A(Staged)--> |Users| B{Dry-run}
        A--> |Groups| B{Dry-run}
        A--> |Projects| B{Dry-run}
        B --> |Users| C(Dry-run logs)
        B --> |Groups| D(Dry-run logs)
        B --> |Projects| E(Dry-run logs)
```

### Migrate users

```eval_rst
.. mermaid::

    graph TD
        A(Stage ALL Users) --> B{Inspect}
        B --> |Found| C(Skip)
        B --> |Not found| D{Remove inactive?}
        D --> |Yes| E(Remove, Dry-run & Inspect)
        E --> F(Migrate)
        D --> |No| G(Dry-run & Inspect)
        G --> H(Migrate and block on destination)
```

### Migrate groups & sub-groups

```eval_rst
.. mermaid::

    graph TD
        A(Stage ALL top-level groups w/ sub-groups) --> B(Dry-run & Inspect)
        B --> C(Migrate)
```

### Migrate projects

```eval_rst
.. mermaid::

    graph TD
        A(Stage Projects) --> |All| B(Dry-run & Inspect)
        B --> C(Migrate)
        A --> |Waves| D{Break into waves}
        D --> E(Dry-run & Inspect)
        E --> F(Migrate Wave 1)
        D --> G(Dry-run & Inspect)
        G --> H(Migrate Wave 2)
        D --> I(Dry-run & Inspect)
        I --> J(Migrate Wave n)
```

### Rollback

```eval_rst
.. mermaid::

    graph TD
        A(Migrated users) --> B{Hard delete}
        B --> |Yes| C(Dry-run & Inspect)
        C --> D(Rollback with contributions)
        B --> |No| E(Dry-run & Inspect)
        E --> F(Rollback)
        G(Migrated groups) --> H(Dry-run & Inspect)
        H --> I(Rollback)
        J(Migrated projects) --> K(Dry-run & Inspect)
        K --> L(Rollback)
```

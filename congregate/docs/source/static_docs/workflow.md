# Migration Workflow

## Pre-migration steps

```eval_rst
.. mermaid::

    graph TD
        A[Pre-migration steps] --> B[Define number of threads]
        A --> C[Remove blocked users]
        A --> D(Check for migration conflicts)
```

## Users Migration

```eval_rst
.. mermaid::

    graph TD
        A[1. Stage all Users] -->L(Check Missing users)
        L -->|User Found| H(No action: All users exists in destination)
        L -->|User Not Found| B(Migrate all missing users)
        L --> |Blocked users|M(Not migrated)
        J[2. Dry Run] --> C(Map Users to respective Projects and Groups)
        D[3. Trigger Migration]
					
```

## Groups Migration

```eval_rst
.. mermaid::

    graph TD
        A[Stage all Groups] --> B[Recreate Groups on destination]
        B --> C[Remove imported admin token]
        C --> D[Add members back to their groups]
        D --> E[Migrate CI variables and group badges]
        E --> F[Enable/Disable Shared runners]
        F --> G[Reset notification level]
```

## Projects Migration

```eval_rst
.. mermaid::

    graph TD
        A[1. Export Projects to Export location. For ex. AWS S3] --> B[2. Remap Projects locally]
        B -->|To fix mapping issues|C(Edit project.json)
        D[3. Re-upload Projects to S3] --> E{Output Status}
        E -->|Fail|F(Rework on failed Project separately and migrate later)
        E -->|Pass|G(Export completed)
        H[4. Project Import] --> I(Remove imported admin token)
        I --> J(Update Project badges, default branch, CI variables)
        J --> K(Update MR approvers, scheduled pipelines, container registry, Awards, Deploy Keys)
```
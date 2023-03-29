# Troubleshooting

## Live reloading for UI development and backend development without a debugger

You will need to turn on debugging in the flask app to see a mostly live reload of the UI. Create the following environment variable before deploying the UI

```bash
export FLASK_DEBUG=1
```

For the UI, you will still need to save the file in your editor and refresh the page, but it's better than restarting flask every time. The app will live reload every time a .py file is changed and saved.

## Configuring VS Code for Debugging

Refer to [this how-to](https://code.visualstudio.com/docs/python/debugging) for setting up the base debugging settings for a python app in VS Code. Then replace the default `launch.json` flask configuration for this:

```json

{
    "name": "Python: Flask (0.11.x or later)",
    "type": "python",
    "request": "launch",
    "module": "flask",
    "env": {
        "PYTHONPATH": "${workspaceRoot}",
        "CONGREGATE_PATH": "<path_to_congregate>",
        "FLASK_APP": "${CONGREGATE_PATH}/ui"
    },
    "args": [
        "run",
        "--no-debugger",
        "--no-reload"
    ]
}

```

To reload the app in debugging mode, you will need to click the `refresh` icon in VS code (on the sidebar's Explorer tab). Currently VS code doesn't support live reloading flask apps on save.

## If VS Code doesn't pick up poetry virtualenv

Find `virtualenv` path

```bash
poetry config --list
```

Add the following line to .vscode/settings.json:

```text
"python.venvPath": "/path/to/virtualenv"
```

You may need to refresh VS Code. VS Code will also call this python interpreter PipEnv, but if you check out the virtualenv directory poetry has stored, you can compare the virtualenv folder names to double check.

## Debugging through the terminal (Python's byebug)

You can import `pdb` into the class you want to debug through a terminal and add `pdb.set_trace()` around the lines you would like to debug.
You can read more about using pdb [here](https://fuzzyblog.io/blog/python/2019/09/24/the-python-equivalent-of-byebug-is-pdb-set-trace.html)

## Setting up bitbucket server for development

Refer to [this README](./docker/bitbucket/README.md) for details on setting up a BitBucket server for local development

## Issues with installing node dependencies

You can delete the `node_modules` folder and re-run `npm install` in the `frontend` directory if you are experiencing issues with frontend dependencies.
If you are still having issues with getting the UI to build correctly after re-installing the dependencies and you don't have any linting issues,
reach out to a maintainer or create an issue pinging `@leopardm` or `@pprokic`.

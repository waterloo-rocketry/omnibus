# Contributing
Welcome to Omnibus! To get started, follow these steps:

1. Clone this repo.
    * If you have git configured with SSH, run `git clone git@github.com:waterloo-rocketry/omnibus.git`
    * If you don't have git configured with SSH (or you're not sure what that means), run `git clone https://github.com/waterloo-rocketry/omnibus.git`
2. Enter the newly-cloned repo with `cd omnibus`
3. Run `pip install wheel`, which will help install the rest of the packages more quickly.
4. Install Python dependencies with `pip install -r requirements.txt`. If you get a permissions error, try `pip install --user -r requirements.txt` instead.
5. Install the Omnibus library locally with `pip install -e .`. Don't forget the `.`! This allows the sources and sinks (and you) to import Omnibus.

You should now be ready to start developing!

* To run unit tests: `pytest`
* To launch the Omnibus server: `python -m omnibus`
* To run a source/sink: `python sources/name/main.py`

# Style guide
If you'd like to contribute to Omnibus, please take a moment to read through this style guide. Otherwise, happy devving :)

### Python
We generally conform to [PEP8](https://pep8.org/) guidelines for how we format our Python code. The repository contains a custom formatting script (`tools/format.sh`) - you should run this optionally before commits, and definitely before creating pull requests and/or merging to master.

When adding code, make sure to add unit tests to match! It's generally a good idea to run the full suite of unit tests before creating a PR (which can be done with the `pytest` command). If you don't, CI will run it for you, but it'll take much longer. We'll get a Slack notification if a failing build makes it to master (but this is fairly unlikely), so don't be too scared of breaking things. They're always fixable :).

### Git
Generally, commit messages should follow guidelines laid out by Chris Beams [here](https://chris.beams.io/posts/git-commit/). Additionally,
* Pull requests should be squashed and merged to be added as commits to master. If the PR pertains to code inside the `omnibus/`, `sources/` or `sinks/` directories (_not_ the main repo), the commit message should be of the form `<subsystem>: <Commit message> (#XX)`, where `<subsystem>` is the folder that the code is relevant to and `XX` is the PR number. `<Commit message>` is the commit message as normal, following regular message guidelines (capital first letter, no period, etc).

    An example commit message could be `plotter: Add custom dashboards (#42)`, for a PR that affects code inside the `sinks/plotter/` directory.
    Commit messages for code outside the `omnibus/`, `sources/` or `sinks/` directories don't need to follow this format. This is mainly to ensure that changes are immediately recognizable reading commit messages from the top level of the repository.

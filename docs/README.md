# Documentation Release Action

This action will generate markdown release posts for your set of software packages,
and save to a Jekyll site posts directory.

## How does it work?

By way of adding a [contributor-ci.yaml](contributor-ci.yaml) with a listing of repos we are interested in,
we can then use the action to (nightly) check for new releases, and given a new release is found,
to add them to a `_posts` folder. We provide an example alongside the action
here under `examples/docs` E.g.,:


```bash
ls ../examples/docs
  2022-03-04-flux-sched-0.21.1.md
  2022-04-04-flux-core-0.38.0.md
  2022-04-08-flux-accounting-0.15.0.md
  2022-04-11-flux-sched-0.22.0.md
  2022-05-06-flux-accounting-0.16.0.md
  2022-05-06-flux-core-0.39.0.md
```

that shows you the output format of our markdown files - we have the full date, project name, and version.
Note that since some repos require special parsing (e.g., the flux-framework org parses a NEWS.md referenced in
the release notes) we provide a set of named, custom parsing functions. E.g., this says to assume
this special format:

```yaml
# Parsing functions to use (e.g, parse a NEWS.md)
functions:
  flux-framework/flux-core: linked-news-markdown-rst
  flux-framework/flux-sched: linked-news-markdown-rst
  flux-framework/flux-accounting: linked-news-markdown-rst
  flux-framework/flux-pmix: linked-news-markdown-rst
```

By default, specifying no custom parser will just use the body of your release
notes (recommended). If there are one of cases for the above that NEWS.md is
not found, we fall back to using the raw body.

## Usage

### GitHub Action

This script is primarily meant to be used as a GitHub action! Here are variables allowed:

| Name     | Description | Required | Default |
|----------|-----------|------------|---------|
| token    | GitHub token | true    | unset   |
| repos    | Path to contributor-ci.yaml file with repos index | true | contributor-ci.yaml |
| author   | Name of author | false | unset |
| categories | Comma separated list of categories (no spaces) for the post | false | release |
| layout   | Post layout to use. Default to unset (no layout, uses default site sets for posts) | false | unset |
| outdir   | Output directory for posts (defaults to _posts in root)  | false | _posts |
| dry_run  | Don't open a pull request - just generate files. | false | false |
| start_at | Date string in format (YYYY-MM-DD) or YYYY to start parsing.  | false | unset |
| branch | branch to open a pull request to | false | main |
| template | use a custom template (should expect same variables as default) | false | template.md in repo here |


Here is how you might use it in an action:

```yaml
name: Update Docs
on:
  schedule:
    - cron: 23 2 * * *

jobs:
  update-release-docs:
    name: Generate posts for flux projects
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v3

      - name: Clone flux-framework.github.io
        run: git clone https://github.com/flux-framework/flux-framework.github.io /tmp/flux

      - name: Flux projects update
        uses: rse-ops/release-actions/docs@main
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          outdir: /tmp/flux/_posts
          author: flux-framework
          layout: default
          start_at: 2022

          # These are defaults
          # repos: ./contributor-ci.yaml
          # dry_run: false

```

### Locally

If you want to use the action script locally - you can! Make sure to install dependencies:

```bash
$ pip install -r requirements.txt
```

And then run against your contributor-ci.yaml (with repos populated) and the output directory:

```bash
$ python ./scripts/make_release_docs.py --repos ../contributor-ci.yaml --outdir ../examples/docs/_posts
```

If you want to start at a particular date, either a `YYYY-MM-DD` or `YYYY-MM` or `YYYY` you can add `--start-at`.
For example, this would only add releases after 2021 (implied January 1st):

```bash
$ python ./scripts/make_release_docs.py --repos ../contributor-ci.yaml --outdir ../examples/docs/_posts --start-at 2022
```

Note that there are many ways you can customize the output, everything from the variables to the
template markdown that you use (see [template.md](template.md) for the default we use).

```bash
$ python docs/scripts/make_release_docs.py --help
usage: make_release_docs.py [-h] [--outdir OUTDIR] [--start-at START_AT] [--author AUTHOR] [--categories CATEGORIES]
                            [--layout LAYOUT] [--repos REPOS]

Release Docs Updater

optional arguments:
  -h, --help            show this help message and exit
  --outdir OUTDIR       output directory with release markdown files.
  --start-at START_AT   optional start date (YYYY-MM-DD) to start parsing at.
  --template TEMPLATE   custom template to use instead of default
  --author AUTHOR       post author (optional)
  --categories CATEGORIES
                        post categories, comma separated with no spaces.
  --layout LAYOUT       layout for post, if desired to change from default.
  --repos REPOS         path for contributor-ci.yaml that has repos key
```

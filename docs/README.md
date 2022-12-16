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
$ python ./scripts/make_release_docs.py --repos ../contributor-ci.yaml --outdir ../examples/docs/_posts --start-at 2021
```

Note that there are many ways you can customize the output, everything from the variables to the
template markdown that you use (see [template.md](template.md) for the default we use).

```bash
$ python docs/scripts/make_release_docs.py --help
usage: make_release_docs.py [-h] [--outdir OUTDIR] [--start-at START_AT] [--author AUTHOR] [--categories CATEGORIES]
                            [--title TITLE] [--layout LAYOUT] [--repos REPOS]

Spack Updater for Releases

optional arguments:
  -h, --help            show this help message and exit
  --outdir OUTDIR       output directory with release markdown files.
  --start-at START_AT   optional start date (YYYY-MM-DD) to start parsing at.
  --template TEMPLATE   custom template to use instead of default
  --author AUTHOR       post author (optional)
  --categories CATEGORIES
                        post categories, comma separated with no spaces.
  --title TITLE         heading to put on page (title is automatically generated)
  --layout LAYOUT       layout for post, if desired to change from default.
  --repos REPOS         path for contributor-ci.yaml that has repos key
```

**under development** - action is coming next!
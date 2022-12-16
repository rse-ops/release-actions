#!/usr/bin/env python3

import argparse
import requests
import yaml
from datetime import datetime
from jinja2 import Template
import re
import sys
import os

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from functions import special_parsing

# Look for version updates for software and generate posts!
# Usage:
# python ./scripts/make_release_docs.py --repos ../contributor-ci.yaml --outdir ../examples/docs/_posts


token = os.environ.get("GITHUB_TOKEN")
headers = {}
if token:
    headers["Authorization"] = "token %s" % token


def read_yaml(filename):
    """
    Load a yaml from file, roundtrip to preserve comments
    """
    with open(filename, "r") as fd:
        content = yaml.load(fd.read(), Loader=yaml.SafeLoader)
    return content


def write_file(data, filename):
    """
    Write content to file
    """
    with open(filename, "w") as fd:
        fd.writelines(data)


def read_file(filename):
    """
    Read content from file
    """
    with open(filename, "r") as fd:
        content = fd.read()
    return content


def set_env_and_output(name, value):
    """
    helper function to echo a key/value pair to output and env.

    Parameters:
    name (str)  : the name of the environment variable
    value (str) : the value to write to file
    """
    for env_var in ("GITHUB_ENV", "GITHUB_OUTPUT"):
        environment_file_path = os.environ.get(env_var)
        print("Writing %s=%s to %s" % (name, value, env_var))

        with open(environment_file_path, "a") as environment_file:
            environment_file.write("%s=%s\n" % (name, value))


class PostGenerator:
    def __init__(self, repos, outdir, start_at=None):
        self._repos_file = os.path.abspath(repos)
        self.repos = {}

        # Lookup of existing markdowns by repo
        self.existing = {}
        self.outdir = os.path.abspath(outdir)
        self.read_repos()
        self.discover_existing()
        self.start_at = start_at
        self.parse_dates()

    def read_repos(self):
        """
        Read the yaml file with a listing of repos.
        """
        content = read_yaml(self._repos_file)
        repos = content.get("repos")
        # We consider this an error - why use the action without repos?
        if not repos:
            sys.exit("No repos found to update.")
        self.repos = repos
        self.functions = content.get("functions", {})

    def within_range(self, release):
        """
        Given a datestring, determine if it's later than the start_at date.
        """
        if not self.start_at:
            return True
        created_at = self.parse_created_at_date(release)
        return created_at > self.start_at

    def parse_created_at_date(self, release):
        """
        Parse and return the created at date.
        """
        created_at = release["created_at"]
        # We only care about day
        created_at = created_at.split("T", 1)[0]
        return datetime.strptime(created_at, "%Y-%m-%d")

    def parse_dates(self):
        """
        Parse the start at date into a datetime
        """
        if not self.start_at:
            return

        # YYYY
        if len(self.start_at) == 4:
            self.start_at = datetime.strptime(self.start_at, "%Y")

        # YYYY-MM
        elif len(self.start_at) == 7:
            self.start_at = datetime.strptime(self.start_at, "%Y-%m")

        # YYYY-MM-DD
        elif len(self.start_at) == 10:
            self.start_at = datetime.strptime(self.start_at, "%Y-%m-%d")
        else:
            sys.exit("Invalid start_at, must be YYYY-MM-DD, YYYY-MM, or YYYY")

    def update_docs(
        self, template, layout=None, title=None, categories=None, author=None
    ):
        """
        Main function to update docs.
        """
        for reponame in self.repos:

            # We assume the repo name is enough
            org, repo = reponame.split("/", 1)

            print(f"Looking for releases for {reponame}")
            releases = self.get_releases(reponame)
            for release in releases:

                # These releases start with v
                tag = tag_bare = release["tag_name"]
                if tag.startswith("v"):
                    tag_bare = re.sub("^v", "", tag)
                if tag in self.existing.get(repo, {}) or tag_bare in self.existing.get(repo, {}):
                    continue

                if not self.within_range(release):
                    continue
                print(f"Found new release {tag} for {repo}")

                # Do we have a special parsing function?
                func = self.functions.get(reponame)
                self.write_release(
                    release=release,
                    repo=repo,
                    template=template,
                    func=func,
                    layout=layout,
                    title=title,
                    categories=categories,
                    author=author,
                )

    def get_version(self, release):
        """
        Get the version of the tag
        """
        version = release["tag_name"]
        if version.startswith("v"):
            version = re.sub("^v", "", version)
        return version

    def write_release(
        self,
        func,
        repo,
        release,
        template,
        layout=None,
        title=None,
        categories=None,
        author=None,
    ):
        """
        Write the release from the body
        """
        version = self.get_version(release)
        body = release["body"]
        if func and func in special_parsing:
            body = special_parsing[func](body, version)

        download_url = release["assets"][0]["browser_download_url"]
        print(download_url)

        render = {
            "notes": body,
            "title": release["name"],
            "author": author,
            "categories": categories,
            "layout": layout,
            "header": title,
            "download_url": download_url,
            "version": version,
            "datestr": str(datetime.now()),
        }
        with open(template, "r") as fd:
            template = Template(fd.read())
        result = template.render(**render)

        created_at = self.parse_created_at_date(release)
        datestr = created_at.strftime("%Y-%m-%d")
        outfile = os.path.join(self.outdir, f"{datestr}-{repo}-{version}.md")
        print(f"Writing {outfile} to file.")
        write_file(result, outfile)

    def discover_existing(self):
        """
        Discover existing release docs (that we don't need) in the outdir.
        """
        # We assume a flat structure for now
        for filename in os.listdir(self.outdir):
            if re.search("[0-9]{4}-[0-9]{2}-[0-9]{2}-.*md", filename):
                filename = filename.rsplit(".", 1)[0]
                year, month, day, rest = filename.split("-", 3)
                project, version = rest.rsplit("-", 1)
                if project not in self.existing:
                    self.existing[project] = set()
                self.existing[project].add(version)

    def get_releases(self, repo):
        """
        Get the latest release of a repository

        These are sorted with the latest at the top.
        """
        page = 1
        releases = []
        while True:
            url = f"https://api.github.com/repos/{repo}/releases"
            print(f"Page {page} of {url}")
            response = requests.get(
                url, headers=headers, params={"per_page": 100, "page": page}
            )
            response.raise_for_status()
            content = response.json()
            releases += content
            if len(content) != 100:
                break
            page += 1
        return releases


def get_parser():
    parser = argparse.ArgumentParser(
        description="Spack Updater for Releases",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--outdir",
        help="output directory with release markdown files.",
        default="_posts",
    )
    parser.add_argument(
        "--start-at",
        help="optional start date (YYYY-MM-DD) to start parsing at.",
        dest="start_at",
    )
    parser.add_argument(
        "--template",
        help="custom template to use instead of default",
        default="template.md",
    )
    parser.add_argument("--author", help="post author (optional)")
    parser.add_argument(
        "--categories", help="post categories, comma separated with no spaces."
    )
    parser.add_argument(
        "--title", help="heading to put on page (title is automatically generated)"
    )
    parser.add_argument(
        "--layout", help="layout for post, if desired to change from default."
    )
    parser.add_argument(
        "--repos",
        help="path for contributor-ci.yaml that has repos key",
        default="contributor-ci.yaml",
    )
    return parser


# python ./scripts/make_release_docs.py --repos ../contributor-ci.yaml --outdir ../examples/docs/_posts


def main():

    parser = get_parser()

    # If an error occurs while parsing the arguments, the interpreter will exit with value 2
    args, extra = parser.parse_known_args()

    # Show args to the user
    print("     title: %s" % (args.title or "no title set"))
    print("     repos: %s" % args.repos)
    print("    author: %s" % (args.author or "no author set"))
    print("    outdir: %s" % args.outdir)
    print("    layout: %s" % (args.layout or "no layout set"))
    print("  template: %s" % args.template)
    print("  start-at: %s" % (args.start_at or "not set"))
    print("categories: %s" % (args.categories or "no categories set"))

    repos = os.path.abspath(args.repos)

    # Cut out early if we don't have repos file
    for path in repos, args.template:
        if not os.path.exists(path):
            sys.exit(f"{path} does not exist.")

    categories = []
    if args.categories:
        categories = args.categories.split(",")

    gen = PostGenerator(repos=args.repos, outdir=args.outdir, start_at=args.start_at)
    gen.update_docs(
        args.template,
        layout=args.layout,
        title=args.title,
        categories=categories,
        author=args.author,
    )


if __name__ == "__main__":
    main()

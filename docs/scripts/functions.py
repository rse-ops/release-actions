import requests
import re
import sys


def return_failure(repo, version):
    print(f"Cannot find NEWS.md in body for {repo}@{version}.")
    return


def linked_news_markdown_rst(body, repo, version):
    """
    Parse a NEWS.md in the body with a ---- separator
    """
    if "NEWS.md" not in body:
        return body

    body = [x for x in body.split("\n") if "NEWS.md" in x]
    if not body:
        return return_failure(repo, version)

    news_link = body[0].split("NEWS.md", 1)[0] + "NEWS.md)"
    match = re.search("(?P<url>https?://[^\s]+)?[)]", news_link)
    if not match:
        return return_failure(repo, version)

    url = match.group("url")
    url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob", "")
    response = requests.get(url)
    if response.status_code != 200:
        return return_failure(repo, version)

    body = response.text

    # For flux, we cut at the first "---"
    notes = []
    lines = body.split("\n")
    for i, line in enumerate(lines):
        if version in line:
            if i != 0:
                notes += [lines[i - 1], line, lines[i + 1]]
            else:
                notes += [line, lines[i + 1]]
            break

    # Next add up to the next ----
    for line in lines[i + 2 :]:
        if "---" in line:
            break
        notes.append(line)
    notes = notes[:-1]

    # For each note, find an issue in parens, change to a full link
    updated = []
    for line in notes:
        match = re.search("[(][#][0-9]+[)]", line)
        if match:
            # Assemble the new link - issues already redirect to PRs
            number = line[match.start() + 2 : match.end() - 1]
            issue_url = f"https://github.com/{repo}/issues/{number}"
            line = (
                line[: match.start()]
                + f"([#{number}]({issue_url}))"
                + line[match.end() :]
            )

        updated.append(line)

    body = "\n".join(updated)
    return body


# List of special parsing functions
# We could allow a repo to provide a custom function if needed.
special_parsing = {"linked-news-markdown-rst": linked_news_markdown_rst}

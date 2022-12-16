import requests
import re
import sys


def linked_news_markdown_rst(body, version):
    """
    Parse a NEWS.md in the body with a ---- separator
    """
    if "NEWS.md" not in body:
        return body
    body = [x for x in body.split("\n") if "NEWS.md" in x]
    if not body:
        sys.exit("Cannot find NEWS.md in body.")
    match = re.search("(?P<url>https?://[^\s]+)?[)]", body[0])
    if not match:
        sys.exit("Cannot find NEWS.md in body.")
    url = match.group("url")
    url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob", "")
    response = requests.get(url)
    if response.status_code != 200:
        sys.exit("Cannot find NEWS.md in body.")
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
    body = "\n".join(notes)
    return body


# List of special parsing functions
# We could allow a repo to provide a custom function if needed.
special_parsing = {"linked-news-markdown-rst": linked_news_markdown_rst}

#!/usr/bin/env python
import os


pre_amble = """
require ["envelope", "imap4flags", "fileinto", "reject", "regex"];

if address :is "to" ["{primary_email}"] {{
    keep;
"""

base_directives = """
}} elsif address :is "to" [ {addrs} ] {{
    fileinto "{folder}";
"""


drop_directives = """
}} elsif address :is "to" [ {addrs} ] {{
    discard;
    stop;
"""

custom_directives = """
} elsif address :regex "to" [".*[0-9]+.*@gr.ht", "[grhtGRHT]{2,}@gr.ht"] {
    fileinto "junk";
"""


post_script = """
} elsif header :contains "Authentication-Results" "dkim=pass" {
    fileinto "bulk";
} else {
    fileinto "junk";
}
"""


def generate(moves, drops, primary_email=None):
    if primary_email is None:
        primary_email = os.getenv("ACCMAIL_EMAIL", "postmaster@example.org")

    out = pre_amble.format(primary_email=primary_email)

    for f in sorted(set(moves.values())):
        rules = []
        for email, folder in moves.items():
            if f == folder:
                rules.append(f'"{email}"')
        out += base_directives.format(addrs=",\n    ".join(sorted(rules)), folder=f)
    autodrops = []
    for each in drops:
        autodrops.append(f'"{each}"')
    out += drop_directives.format(addrs=",\n    ".join(sorted(autodrops)))

    out += custom_directives
    out += post_script
    return out


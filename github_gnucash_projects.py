from getpass import getpass
import json
import datetime

import requests

client_id = "sdementen"

if __name__=='__main__':
    languages = {}
    client_secret = getpass("Enter password for user '{}' :".format(client_id))
    i = 0
    for pg in range(100):
        url = "https://api.github.com/search/repositories?q=gnucash&sort=stars&order=desc&page={}&per_page=100?client_id={}&client_secret={}".format(
            pg + 1, client_id, client_secret)
        response = requests.get(url)
        res = json.loads(response.text)
        try:
            projects = res["items"]
        except KeyError:
            break
        if not res["items"]:
            break

        for project in projects:
            if (project["name"].lower() == "gnucash") or ("mirror" in (project["description"] or "").lower()):
                continue
            i += 1
            languages.setdefault(project["language"], []).append(project)

    with open("docs/source/doc/github_links.rst", "w") as fo:
        list_of_projects = sorted([(k or "", v) for k, v in languages.items()],
                                  key=lambda v: ("AAA" if v[0] == "Python" else v[0] or "zzz"))

        width = 30
        sep_row = "+" + "-" * width
        head_row = "+" + "=" * width
        row = "|" + " " * width

        print("Projects per language", file=fo)
        print("=====================", file=fo)
        print(file=fo)
        print("This page lists all projects found by searching 'gnucash' on github (generated on {})"
              "excluding mirrors of the gnucash repository".format(datetime.datetime.today().replace(microsecond=0)),
              file=fo)
        print(file=fo)
        print(sep_row + sep_row + sep_row + "+", file=fo)
        print("|{:^30}|{:^30}|{:^30}|".format("Language", "# of projects", "# of projects updated in 2014"), file=fo)
        print(head_row + head_row + head_row + "+", file=fo)

        for lang, projects in list_of_projects:
            recent_projects = [pr for pr in projects if pr["updated_at"] >= "2014-01-01"]
            print("|{:^30}|{:^30}|{:^30}|".format(":ref:`{}`".format(lang), len(projects), len(recent_projects)), file=fo)
            print(sep_row + sep_row + sep_row + "+", file=fo)

        print(file=fo)

        for lang, projects in list_of_projects:
            print(lang)
            print(".. _{}:".format(lang or "Unknown"), file=fo)
            print(file=fo)
            print(lang or "Unknown", file=fo)
            print("-" * len(lang or "Unknown"), file=fo)
            print(file=fo)
            for i, project in enumerate(sorted(projects, key=lambda pr: pr["name"])):
                updated_at = project["updated_at"][:10]
                user = project["owner"]["login"]
                description = project["description"] or "(No description available)"
                name = project["name"]
                html_url = project["html_url"]
                print("`{name} <{html_url}>`__ by {user} (last updated on  {updated_at:<10})\n"
                      "\t{description}".format(i + 1, user=user, updated_at=updated_at, description=description,
                                               name=name, html_url=html_url),
                      file=fo)
            print(file=fo)

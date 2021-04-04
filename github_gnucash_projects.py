import datetime
import os

from github import Github

if __name__ == "__main__":
    languages = {}

    try:
        GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
    except KeyError:
        raise ValueError(
            "You should have a valid Github token in your GITHUB_TOKEN environment variable"
        )

    g = Github(GITHUB_TOKEN)
    for project in g.search_repositories(query="gnucash", sort="stars", order="desc"):
        print(project)
        if (project.name.lower() == "gnucash") or (
            "mirror" in (project.description or "").lower()
        ):
            continue
        languages.setdefault(project.language, []).append(project)

    with open("docs/source/doc/github_links.rst", "w", encoding="UTF-8") as fo:
        list_of_projects = sorted(
            [(k or "", v) for k, v in languages.items()],
            key=lambda v: ("AAA" if v[0] == "Python" else v[0] or "zzz"),
        )

        width = 50
        sep_row = "+" + "-" * width
        head_row = "+" + "=" * width
        row = "|" + " " * width

        print("Projects per language", file=fo)
        print("=====================", file=fo)
        print(file=fo)
        print(
            "This page lists all projects found by searching 'gnucash' on github (generated on {}) "
            "excluding mirrors of the gnucash repository. Projects with a '\*' are projects "
            "that have not been updated since 12 months.".format(
                datetime.datetime.today().replace(microsecond=0)
            ),
            file=fo,
        )
        print(file=fo)
        print(sep_row + sep_row + sep_row + "+", file=fo)
        print(
            "|{:^50}|{:^50}|{:^50}|".format(
                "Language", "# of projects", "# of projects updated in last 12 months"
            ),
            file=fo,
        )
        print(head_row + head_row + head_row + "+", file=fo)

        last12month = datetime.datetime.today() - datetime.timedelta(days=365)
        list_of_projects = [
            (
                lang or "Unknown",
                projects,
                {pr.html_url for pr in projects if pr.pushed_at >= last12month},
            )
            for (lang, projects) in list_of_projects
        ]

        for lang, projects, recent_projects in sorted(
            list_of_projects, key=lambda k: -len(k[2])
        ):
            print(
                "|{:^50}|{:^50}|{:^50}|".format(
                    ":ref:`{}`".format(lang), len(projects), len(recent_projects)
                ),
                file=fo,
            )
            print(sep_row + sep_row + sep_row + "+", file=fo)

        print(file=fo)

        for lang, projects, recent_projects in list_of_projects:
            print(lang)
            print(".. _{}:".format(lang), file=fo)
            print(file=fo)
            print(lang or "Unknown", file=fo)
            print("-" * len(lang or "Unknown"), file=fo)
            print(file=fo)
            for project in sorted(projects, key=lambda pr: pr.name.lower()):
                description = project.description or "(No description available)"
                print(
                    "{}`{name} <{html_url}>`__ by {user} (last commit on  {pushed_at:%Y-%m-%d})\n"
                    "\t{description}".format(
                        "" if project.html_url in recent_projects else "\* ",
                        user=project.owner.login,
                        pushed_at=project.pushed_at,
                        description=description,
                        name=project.name,
                        html_url=project.html_url,
                    ),
                    file=fo,
                )
            print(file=fo)

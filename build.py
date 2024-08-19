#!/usr/bin/env python3
"""Build my CV.

All the paths here are hard coded because why not for this?
"""
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from jinja2 import (
    Environment,
    FileSystemLoader,
    select_autoescape,
)
from pybtex.database import Person, Entry
from pybtex.database.input import bibtex

TEX = Path("fondrie_cv.tex")
BIB = Path("pubs.bib")
PRES = Path("presentations.json")
PREPRINT_SERVERS = {"biorxiv", "arxiv", "chemrxiv"}

COFIRST = {
    "10.1101/2023.01.03.522621": 2,
    "10.1021/acs.analchem.5b02586": 2,
}


@dataclass
class Presentation:
    """A single presentation"""
    authors: list[str]
    kind: str
    title: str
    venue: str
    location: str
    year: str
    month: str
    location: str

    def __post_init__(self) -> None:
        """Process the author list."""
        people = [format_person(Person(p)) for p in self.authors]
        self.authors = ", ".join(people)

    @property
    def date(self) -> datetime:
        """A proper date by which to sort."""
        datestr = f"{self.year} {self.month}"
        return datetime.strptime(datestr, "%Y %B")

    @property
    def citation(self) -> str:
        """Generate the citation."""
        citation = [
            r"\item ",
            self.authors,
            f". ({self.year}) ",
            self.title.replace("{", "").replace("}", ""),
            ". ",
            r"\textit{" + self.venue + "}, " if self.venue else "",
            self.location,
        ]
        return "".join(citation)

    @classmethod
    def from_json(cls, entry: dict) -> None:
        """Parse the json object"""
        return Presentation(**entry)



@dataclass
class Reference:
    """A single reference."""
    year: str
    month: str
    day: str
    title: str
    volume: str
    issue: str
    doi: str
    pages: str
    journal: str
    authors: list[Person]
    n_star: int | None = None

    def __post_init__(self):
        """Process things that need to be processed"""
        if self.n_star is None:
            self.n_star = COFIRST.get(self.doi, None)

        people = []
        for idx, person in enumerate(self.authors):
            person = format_person(person)
            if self.n_star is not None and idx < self.n_star:
                person += "*"

            people.append(person)

        self.authors = ", ".join(people)

    @property
    def date(self) -> datetime:
        """A proper date by which to sort."""
        datestr = f"{self.year} {self.month} {self.day}"
        return datetime.strptime(datestr, "%Y %B %d")

    @property
    def citation(self) -> str:
        """The APA-style citation"""
        citation = [
            r"\item ",
            self.authors,
            f". ({self.year}) ",
            self.title.replace("{", "").replace("}", ""),
            ". ",
            r"\textit{" + self.journal + "}, " if self.journal else "",
            r"\textit{" + self.volume + "}",
            f"({self.issue})," if self.issue else "",
            f"{self.pages}. " if self.pages else "",
            "https://doi.org/" + self.doi if self.doi else "",
        ]
        return "".join(citation)

    @property
    def citation_type(self) -> str:
        """The type of citation this is."""
        if (self.journal.lower() in PREPRINT_SERVERS):
            return "preprint"

        if self.title.lower().startswith("biological insight from mass"):
            return "dissertation"

        return "article"

    @classmethod
    def from_entry(cls, entry: Entry, n_star: int | None = None) -> None:
        """Parse a Bibtex entry."""
        fields = entry[1].fields

        try:
            journal = fields["journal"]
        except KeyError:
            if fields.get("type", "") == "Preprint":
                journal = "bioRxiv"
            else:
                journal = fields.get("booktitle", "")

        return Reference(
            year=fields["year"],
            month=fields.get("month", "January"),
            day=fields.get("day", "1"),
            title=fields["title"],
            volume=fields.get("volume", ""),
            issue=fields.get("number", ""),
            doi=fields.get("doi", ""),
            pages=fields.get("pages", ""),
            journal=journal,
            authors=entry[1].persons["author"],
            n_star=n_star
        )


def format_person(person: Person) -> str:
    """Format a Person to a string.

    Parameters
    ----------
    person : Person
        The Person object to format

    Returns
    -------
    str
        The name in the "Last, FM" format.
    """
    last = " ".join(person.last_names)
    first = "".join([n[0] for n in person.first_names])
    middle = "".join([n[0] for n in person.middle_names])
    name = f"{last} {first}{middle}"

    if last == "Fondrie":
        name = r"\textbf{" + name + "}"

    return name


def sort_refs(refs: dict):
    """Sort the lists of refs by date."""
    for kind in refs.values():
        kind.sort(reverse=True, key=lambda x: x.date)

    out = {}
    for kind, data in refs.items():
        out[kind] = [r.citation for r in data]

    return out


def main():
    """Build the CV."""
    # Parse the publications:
    parser = bibtex.Parser()
    pubs = defaultdict(list)
    for pub in parser.parse_file(BIB).entries.items():
        ref = Reference.from_entry(pub)
        pubs[ref.citation_type].append(ref)

    # Parse the presentations:
    presentations = defaultdict(list)
    with PRES.open() as pres_data:
        for pres in json.load(pres_data):
            ref = Presentation.from_json(pres)
            presentations[ref.kind].append(ref)

    # Render the template:
    pubs = sort_refs(pubs)
    presentations = sort_refs(presentations)

    loader = FileSystemLoader(searchpath="./")
    env = Environment(loader=loader, autoescape=select_autoescape())
    template = env.get_template("fondrie_cv.template.tex")
    print(pubs.get("preprint"), "")
    rendered = template.render(
        articles="\n\n".join(pubs["article"]),
        preprints="\n\n".join(pubs.get("preprint", [])),
        dissertation="\n\n".join(pubs["dissertation"]),
        invited="\n\n".join(presentations["invited"]),
        talks="\n\n".join(presentations["talk"])
    )

    with Path("fondrie_cv.tex").open("w+") as tex_out:
        tex_out.write(rendered)


if __name__ == "__main__":
    main()

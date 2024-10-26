import requests
from bs4 import BeautifulSoup
import cachetools.func
import dataclasses as dc
import typing as T
from hashlib import sha256


@dc.dataclass
class RitehNovost:
    title: str
    link: str
    summary: str
    date: str

    @property
    def hash(self):
        m = sha256()
        m.update(self.link.encode())
        m.update(self.date.encode())
        return m.hexdigest()


@cachetools.func.ttl_cache(ttl=60)
def get_novosti() -> T.List[RitehNovost]:
    r = requests.get("http://www.riteh.uniri.hr/")
    soup = BeautifulSoup(r.text, "html.parser")

    novosti_ul = soup.findAll("ul")[2].findAll("li")

    novosti = []
    for novost in novosti_ul:
        novosti.append(
            RitehNovost(
                novost.a.text.replace("\xa0", " "),  # Title
                "http://www.riteh.uniri.hr" + novost.a["href"],  # Link
                novost.div.text.replace("\xa0", " "),  # Summary
                novost.dl.dd.text.replace("\xa0", " "),  # Date
            )
        )
    return novosti[::-1]


if __name__ == "__main__":
    get_novosti()

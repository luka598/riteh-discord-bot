import dataclasses as dc
import typing as T
from hashlib import sha256

import cachetools.func
import requests
from bs4 import BeautifulSoup


@dc.dataclass
class RitehNovost:
    title: str
    link: str
    summary: str
    date: str
    img: T.Optional[str]

    @property
    def hash(self):
        m = sha256()
        m.update(self.link.encode())
        m.update(self.title.encode())
        return m.hexdigest()


@cachetools.func.ttl_cache(ttl=60)
def get_novosti() -> T.List[RitehNovost]:
    r = requests.get("http://www.riteh.uniri.hr/")
    soup = BeautifulSoup(r.text, "html.parser")

    novosti_ul = soup.findAll("ul")[2].findAll("li")

    novosti = []
    for novost in novosti_ul:
        title = novost.h3.text.replace("\xa0", " ")
        try:
            link = "http://www.riteh.uniri.hr" + novost.a["href"]
        except:
            link = ""
        summary = novost.div.text.replace("\xa0", " ")
        date = novost.dl.dd.text.replace("\xa0", " ")
        try:
            img = "http://www.riteh.uniri.hr" + novost.img["src"]
        except:
            img = None

        novosti.append(
            RitehNovost(
                title,
                link,
                summary,
                date,
                img,
            )
        )
    return novosti[::-1]


if __name__ == "__main__":
    get_novosti()

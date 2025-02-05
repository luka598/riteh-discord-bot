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
    category: str
    img: T.Optional[str]

    @property
    def hash(self):
        m = sha256()
        m.update(self.link.encode())
        m.update(self.title.encode())
        return m.hexdigest()


@cachetools.func.ttl_cache(ttl=60)
def get_novosti() -> T.List[RitehNovost]:
    novosti = []

    r = requests.get("https://riteh.uniri.hr/novosti/")
    soup = BeautifulSoup(r.text, "html.parser")

    posts = soup.find("div", attrs={"class": "elementor-loop-container elementor-grid"}).find_all("div", attrs={"class": "post"}) # type: ignore
    for post in posts:
        for idx, x in enumerate(post.find_all("div", recursive=False)):
            print("---", idx, x, "\n\n")

        title = post.find("div", attrs={"class": "elementor-widget-theme-post-title"}).text.replace("\n", "")
        title = title.replace("\n", "").replace("\xa0", " ")

        summary = post.find("div", attrs={"class": "elementor-widget-theme-post-excerpt"}).text
        summary = summary.replace("\n", "").replace("\t", "")

        category = post.find("p").text.replace("\n", "")

        link = post.find("a")["href"].replace("\n", "")

        try:
            img = str(post.find("img")["src"])
            if ("elementor-placeholder" in img) or ("uniri-logo-header" in img) or ("UNIRI_Logotip" in img):
                img = None
        except:
            img = None

        novosti.append(RitehNovost(title, link, summary, category, img))

    return novosti[1:][::-1]


if __name__ == "__main__":
    novosti = get_novosti()
    for novost in novosti:
        print(novost.title)
        print(novost.hash)
        print("-")
        print(novost.category)
        print(novost.summary)
        print(novost.img)
        print(novost.link)
        print("===")

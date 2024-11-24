import dataclasses as dc
import typing as T
from hashlib import sha256

import cachetools.func
import requests
from bs4 import BeautifulSoup

DEFAULT_IMG = "https://www.scri.uniri.hr/components/com_jsjobs/images/blank_logo.png"


@dc.dataclass
class Objava:
    novo: bool
    img: T.Optional[str]
    naziv: str
    link: str
    kategorija: str
    objavljeno: T.Union[int, str]
    sanitarna: T.Union[bool, str]
    obrok: T.Union[bool, str]
    smještaj: T.Union[bool, str]
    pocetak: T.Union[int, str]
    mjesto: str
    zavrsetak: T.Union[int, str]
    putni_trosak: T.Union[bool, str]
    poslodavac: str
    cijena_sat: T.Union[float, str]
    cijena_sat_ned: T.Union[float, str]

    @property
    def hash(self) -> str:
        m = sha256()
        m.update(self.link.encode())  # NOTE: Mozda nije dovoljno al bumo vidjeli
        return m.hexdigest()


@cachetools.func.ttl_cache(ttl=60)
def get_jobs() -> T.List[Objava]:
    objave = []

    n = 0
    r = requests.get(
        f"https://www.scri.uniri.hr/student-servis/jobseeker-control-panel/index.php?option=com_jsjobs&task=job.getnextjobs&pagenum={n}"
    )

    soup = BeautifulSoup(r.text, "html.parser")
    jobs = soup.find_all("div", {"id": "js-jobs-wrapper"})
    for job in jobs:
        # novo
        if job.find("span", {"class": "bg-new"}) is None:
            novo = False
        else:
            novo = True

        # img
        img = job.find("img")["src"]
        if img == DEFAULT_IMG:
            img = None

        # naziv
        naziv = job.find("a", {"class": "jobtitle"}).text

        # link
        link = "https://www.scri.uniri.hr" + job.find("a", {"class": "jobtitle"})["href"]

        # ostalo
        ostalo = job.find_all("div", {"class": "js-fields"})
        """
        0 Kategorija posla: RAD NA BLAGAJNI
        1 Posted: 1 Day Ago
        2 Sanitarna knjižica: DA
        3 Obrok: NE
        4 Smještaj: NE
        5 Početak rada: 25-11-2024
        6 Mjesto rada: Plodine, Osječka 50 Rijeka
        7 Završetak rada: Prema dogovoru
        8 Putni trošak: NE
        9 Poslodavac: Plodine d.d.
        10 Cijena redovnog sata u €:: 6,50€
        11 Rad nedjeljom u €:: 9,75€
        """

        # kategorija
        kategorija = ostalo[0].text.lstrip("Kategorija posla: ").lower().capitalize()

        # objavljeno
        objavljeno = ostalo[1].text.lstrip("Posted: ").lower().capitalize()

        # sanitarna
        sanitarna = ostalo[2].text.lstrip("Sanitarna knjižica: ").lower().capitalize()

        # obrok
        obrok = ostalo[3].text.lstrip("Obrok: ").lower().capitalize()

        # smjestaj
        smjestaj = ostalo[4].text.lstrip("Smještaj: ").lower().capitalize()

        # pocetak
        pocetak = ostalo[5].text.lstrip("Početak rada: ").lower().capitalize()

        # mjesto
        mjesto = ostalo[6].text.lstrip("Mjesto rada: ").lower().capitalize()

        # zavrsetak
        zavrsetak = ostalo[7].text.lstrip("Završetak rada: ").lower().capitalize()

        # putni trosak
        putni_trosak = ostalo[8].text.lstrip("Putni trošak: ").lower().capitalize()

        # poslodavac
        poslodavac = ostalo[9].text.lstrip("Poslodavac: ").lower().capitalize()

        # cijena_sat
        cijena_sat = ostalo[10].text.lstrip("Cijena redovnog sata u €:: ").lower().capitalize()

        # cijena_sat_ned
        cijena_sat_ned = ostalo[11].text.lstrip("Rad nedjeljom u €:: ").lower().capitalize()

        objave.append(
            Objava(
                novo,
                img,
                naziv,
                link,
                kategorija,
                objavljeno,
                sanitarna,
                obrok,
                smjestaj,
                pocetak,
                mjesto,
                zavrsetak,
                putni_trosak,
                poslodavac,
                cijena_sat,
                cijena_sat_ned,
            )
        )
    return objave[::-1]


if __name__ == "__main__":
    get_jobs()

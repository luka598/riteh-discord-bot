import requests
from bs4 import BeautifulSoup, Tag
import typing as T
import cachetools.func
from fuzzywuzzy import process

MENZA_NAME_ID = {
    "index": 41,
    "kampus": 42,
    "mini": 43,
    "mul": 44,
    "pravri": 45,
    "riteh": 46,
    "pomorac": 47,
}

FOOD_EMOJI = {
    "juha": "🍜",
    "juha bistra": "🍜",
    "juha proljetna": "🍜",
    "juha rajčica": "🍜🍅",
    "juha od cvjetače": "🍜🥦",
    "juha od brokule": "🍜🥦",
    "pileći rižoto": "🍚",
    "pire krumpir": "🥔",
    "kupus salata": "🥗",
    "salata od svježeg kupusa": "🥗",
    "kruh": "🍞",
    "kruh 3 šnite": "🍞",
    "napolitanke": "🍩",
    "kotlet na samoborski": "🥩",
    "voćni jogurt": "🍓🥛",
    "odrezak od kelja": "🥬",
    "đuveč": "🍚🥕🍅",
    "mrkva salata": "🥗🥕",
    "zelena salata": "🥗",
    "salata od kisele cikle": "🥗",
    "cikla salata": "🥗",
    "tjestenina milanez": "🍝",
    "pileći file na žaru": "🍗",
    "pohani sir": "🧀",
    "salata od kiselih krastavaca": "🥒",
    "odrezak od soje": "🌱",
    "pirjani ječam": "🌾",
    "mahune u umaku": "🌿",
    "krpice sa zeljem": "🍝",
    "kuhana cvjetača": "🥦",
    "pomfrit": "🍟",
    "pureći bečki odrezak": "🍗",
    "pečena piletina": "🍗",
    "tjestenina s mesom": "🍝",
    "svinjski pečenje": "🥓",
    "naravni odrezak": "🥩",
    "juneći gulaš": "🍲",
    "panirane srdele": "🐟",
    "krumpir salata": "🥔🥗",
    "riža": "🍚",
    "paprikaš sa graškom": "🥘🌱",
    "puding čokolada": "🍮",
    "grah varivo s kiselim kupusom": "🍲🥬",
    "kranjske kobasice kuhane": "🌭",
    "kukuruz ,grašak ,mrkva": "🌽🍃🥕",
    "salata s tunom i tjesteninom": "🥗🐟🍝",
    "salata od tune i tjestenine": "🥗🐟🍝",
    "tjestenina": "🍝",
    "tuna i šampinjoni": "🐟🍄",
    "lignje na buzaru": "🦑🍲",
    "musaka": "🍆🥔",
    "rižoto od lignji": "🦑🍚",
    "pečenice": "🌭🔥",
    "varivo grašak": "🍲🌱",
    "njoki": "🥔🍝",
    "kotlet sa šampinjonima": "🥩🍄",
    "mlinci": "️🥟",
    "blitva s krumpirom": "🥬🥔",
    "rizi bizi": "🍚🌱",
    "špageti bolonjez": "🍝",
    "odrezak od tikvica": "🍆",
    "pohani riblji štapići": "🐟",
    "pečena svinjetina": "🥓🔥",
    "čevapi": "🌭🔥🇧🇦",
    "pljeskavica": "🍔",
    "kelj pupčar": "🥬",
    "grašak u umaku s restanim krumpirom": "🌱🥔🧅",
    "kosana štruca": "🍖🍞",
    "sir sa vrhnjem": "🧀🍶",
    "palenta": "🌽",
    "umak od rajčice": "🍅",
    "pečeni krompir": "🥔",
}


@cachetools.func.lfu_cache()
def emojify(s: str) -> str:
    s = s.lower()

    if s in FOOD_EMOJI:
        return FOOD_EMOJI[s]
    else:
        best, score = process.extractOne(s, list(FOOD_EMOJI.keys()))  # type: ignore | Type checker je sam tupav
        if score > 50:
            return FOOD_EMOJI[best]

    return "❔"


@cachetools.func.ttl_cache(ttl=60)
def get_meni(menza_name: str):
    menza_id = MENZA_NAME_ID.get(menza_name.lower(), None)
    if menza_id is None:
        return None, None

    r = requests.get(f"https://app.scri.hr/dnevnimeni/{menza_id}")
    soup = BeautifulSoup(r.text, "html.parser")

    def get_table(tag_id: str) -> T.Optional[T.List]:
        table = soup.find("table", id=tag_id)
        if not isinstance(table, Tag):
            return None

        rows = table.find_all("tr")

        table_data = []
        for row in rows:
            cols = row.find_all("td")
            table_data.append(cols)

        meni = []
        for row in table_data:
            meni_name = row[0].text
            meni_content_text = [
                p.text for p in BeautifulSoup(row[1].text, "html.parser").find_all("p")
            ]

            meni_content = []
            for item in meni_content_text:
                if item == "":
                    continue

                item_name = item.split("-")[0].strip().lower().capitalize()
                item_emoji = emojify(item_name)
                meni_content.append((item_name, item_emoji))

            if len(meni_content) != 0:
                meni.append((meni_name, meni_content))

        return meni

    return get_table("tablica"), get_table("tablica2")


if __name__ == "__main__":
    print(get_meni("kampus"))
    print(get_meni("index"))

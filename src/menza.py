import requests
from bs4 import BeautifulSoup, Tag
import typing as T


def get_meni(menza_id: int):
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
            meni_content = [
                p.text for p in BeautifulSoup(row[1].text, "html.parser").find_all("p")
            ]

            while True:
                try:
                    meni_content.remove("")
                except ValueError:
                    break

            if len(meni_content) != 0:
                meni.append((meni_name, meni_content))

        return meni

    return get_table("tablica"), get_table("tablica2")
    # print(tablica_1)


if __name__ == "__main__":
    # print(get_meni(46))
    print(get_meni(46))

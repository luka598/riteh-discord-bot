use scraper::{ElementRef, Html, Selector};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::OnceLock;

use crate::{
    funcs::router::{self, Request, Response},
    route_handler, store, util,
};

#[derive(Debug, Serialize, Deserialize)]
pub struct Menu {
    name: String,
    items: Vec<(String, Vec<String>)>,
}

fn food_emoji() -> &'static HashMap<&'static str, &'static str> {
    static MAP: OnceLock<HashMap<&'static str, &'static str>> = OnceLock::new();
    MAP.get_or_init(|| {
        HashMap::from([
            ("juha", "🍜"),
            ("juha bistra", "🍜"),
            ("juha proljetna", "🍜"),
            ("juha rajčica", "🍜🍅"),
            ("juha od cvjetače", "🍜🥦"),
            ("juha od brokule", "🍜🥦"),
            ("pileći rižoto", "🍚"),
            ("pire krumpir", "🥔"),
            ("kupus salata", "🥗"),
            ("salata od svježeg kupusa", "🥗"),
            ("kruh", "🍞"),
            ("kruh 3 šnite", "🍞"),
            ("napolitanke", "🍩"),
            ("kotlet na samoborski", "🥩"),
            ("voćni jogurt", "🍓🥛"),
            ("odrezak od kelja", "🥬"),
            ("đuveč", "🍚🥕🍅"),
            ("mrkva salata", "🥗🥕"),
            ("zelena salata", "🥗"),
            ("salata od kisele cikle", "🥗"),
            ("cikla salata", "🥗"),
            ("tjestenina milanez", "🍝"),
            ("pileći file na žaru", "🍗"),
            ("pohani sir", "🧀"),
            ("salata od kiselih krastavaca", "🥒"),
            ("odrezak od soje", "🌱"),
            ("pirjani ječam", "🌾"),
            ("mahune u umaku", "🌿"),
            ("krpice sa zeljem", "🍝"),
            ("kuhana cvjetača", "🥦"),
            ("pomfrit", "🍟"),
            ("pureći bečki odrezak", "🍗"),
            ("pečena piletina", "🍗"),
            ("tjestenina s mesom", "🍝"),
            ("svinjski pečenje", "🥓"),
            ("naravni odrezak", "🥩"),
            ("juneći gulaš", "🍲"),
            ("panirane srdele", "🐟"),
            ("krumpir salata", "🥔🥗"),
            ("riža", "🍚"),
            ("paprikaš sa graškom", "🥘🌱"),
            ("puding čokolada", "🍮"),
            ("grah varivo s kiselim kupusom", "🍲🥬"),
            ("kranjske kobasice kuhane", "🌭"),
            ("kukuruz ,grašak ,mrkva", "🌽🍃🥕"),
            ("salata s tunom i tjesteninom", "🥗🐟🍝"),
            ("salata od tune i tjestenine", "🥗🐟🍝"),
            ("tjestenina", "🍝"),
            ("tuna i šampinjoni", "🐟🍄"),
            ("lignje na buzaru", "🦑🍲"),
            ("musaka", "🍆🥔"),
            ("rižoto od lignji", "🦑🍚"),
            ("pečenice", "🌭🔥"),
            ("varivo grašak", "🍲🌱"),
            ("njoki", "🥔🍝"),
            ("kotlet sa šampinjonima", "🥩🍄"),
            ("mlinci", "️🥟"),
            ("blitva s krumpirom", "🥬🥔"),
            ("rizi bizi", "🍚🌱"),
            ("špageti bolonjez", "🍝"),
            ("odrezak od tikvica", "🍆"),
            ("pohani riblji štapići", "🐟"),
            ("pečena svinjetina", "🥓🔥"),
            ("čevapi", "🌭🔥🇧🇦"),
            ("pljeskavica", "🍔"),
            ("kelj pupčar", "🥬"),
            ("grašak u umaku s restanim krumpirom", "🌱🥔🧅"),
            ("kosana štruca", "🍖🍞"),
            ("sir sa vrhnjem", "🧀🍶"),
            ("palenta", "🌽"),
            ("umak od rajčice", "🍅"),
            ("pečeni krompir", "🥔"),
            ("naranča", "🟠"),
            ("oslić", "🐟"),
            ("pohani oslić file", "🐟"),
            ("tortellini sa sirom", "🍝"),
            ("voće jabuka", "🍎"),
            ("pureći bečki", "🥩"),
            ("prijana riža", "🍚"),
            ("tjestenina sa tunom i šampinjonima", "🐟"),
            ("pržena srdela", "🐟"),
            ("čoko puding", "🍮"),
            ("štrudle",  "🍮"),
            ("salata cikla", "🫜"),
            ("salata od kisle cikle", "🫜"),
            ("pileći medaljoni", "🍗"),
            ("proljetna juha", "🍜"),
            ("juha cvijetača", "🍜"),
            ("meksička mješavina", "🌽"),
        ])
    })
}

fn capitalize(s: &str) -> String {
    let lower = s.to_lowercase();
    let mut chars = lower.chars();
    match chars.next() {
        Some(first) => first.to_uppercase().collect::<String>() + chars.as_str(),
        None => String::new(),
    }
}

fn emojify(s: &str) -> &'static str {
    let lower = s.to_lowercase();
    let map = food_emoji();
    if let Some(&e) = map.get(lower.as_str()) {
        return e;
    }
    let keys: Vec<&str> = map.keys().copied().collect();
    if let Some((best, dist)) = util::fuzzy_match(&lower, &keys, 1).into_iter().next() {
        let lensum = lower.chars().count() + best.chars().count();
        if lensum > 0 {
            let score = (lensum - dist) * 100 / lensum;
            if score > 50 {
                if let Some(&e) = map.get(best.as_str()) {
                    return e;
                }
            }
        }
    }
    "❔"
}

fn parse_menu(doc: &Html, table_class: &str) -> Menu {
    let mut res = Menu {
        name: table_class.to_string(),
        items: vec![],
    };

    let table_selector = Selector::parse(&format!("table#{table_class}")).unwrap();
    let row_selector = Selector::parse("tr").unwrap();
    let cell_selector = Selector::parse("td").unwrap();
    let p_selector = Selector::parse("p").unwrap();

    let table: ElementRef = match doc.select(&table_selector).next() {
        Some(x) => x,
        None => return res,
    };

    for row in table.select(&row_selector) {
        let cells: Vec<ElementRef> = row.select(&cell_selector).collect();
        if cells.len() < 2 {
            continue;
        }

        let label = cells[0].text().collect::<String>().trim().to_uppercase();

        if label == "NAZIV" {
            continue;
        }

        let inner_html: String = cells[1].text().collect();
        let inner_doc = Html::parse_fragment(&inner_html);

        let items: Vec<String> = inner_doc
            .select(&p_selector)
            .filter_map(|p| {
                let text = p.text().collect::<String>();
                let text = text.trim();
                if text.is_empty() {
                    return None;
                }
                let item_name = text.split('-').next().unwrap_or("").trim();
                if item_name.is_empty() {
                    return None;
                }
                Some(capitalize(item_name))
            })
            .collect();

        res.items.push((label, items));
    }

    res
}

pub async fn fetch(menza_id: u32) -> (Menu, Menu) {
    let data_key = format!("data:scri_menza:{menza_id}:data");
    let time_key = format!("data:scri_menza:{menza_id}:time");
    let s = store::store().lock().await;

    if let Ok(time_str) = s.get(&time_key) {
        if let Ok(stored) = time_str.parse::<u64>() {
            let now = util::now_ms();
            if now.saturating_sub(stored) < 300_000 {
                if let Ok(val) = s.get(&data_key) {
                    if let Ok((rucak, vecera)) = serde_json::from_str::<(Menu, Menu)>(&val) {
                        return (rucak, vecera);
                    }
                }
            }
        }
    }
    drop(s);

    let url = format!("https://app.scri.hr/dnevnimeni/{menza_id}");
    let body = reqwest::get(&url).await.unwrap().text().await.unwrap();

    let (rucak, vecera) = {
        let doc = Html::parse_document(&body);
        (parse_menu(&doc, "tablica"), parse_menu(&doc, "tablica2"))
    };

    let now = util::now_ms();
    let s = store::store().lock().await;
    if let Ok(json) = serde_json::to_string(&(&rucak, &vecera)) {
        let _ = s.set(&data_key, &json);
        let _ = s.set(&time_key, &now.to_string());
    }

    (rucak, vecera)
}

fn menza_ids() -> HashMap<&'static str, u32> {
    HashMap::from([("index", 41), ("kampus", 42), ("mini", 43), ("mul", 44), ("pravri", 45), ("riteh", 46), ("pomorac", 47)])
}

pub async fn init() {
    let mut r = router::router().write().await;
    r.register_command("menza", route_handler!(menza));
}

async fn menza(r: Request) -> Response {
    let text = match r {
        Request::Message { text, .. } => text,
        _ => return Response::None,
    };
    let menza_name = match text.split_whitespace().nth(1) {
        Some(x) => x.to_lowercase(),
        None => {
            return Response::ReplyEmbed {
                title: "Menza".into(),
                description: format!(
                    "Koji menza? npr. `!menza riteh`\n\nDostupne: {}",
                    menza_ids().keys().map(|k| format!("`{k}`")).collect::<Vec<_>>().join(", ")
                ),
                color: 0xEA2915,
                lines: vec![],
            };
        }
    };

    let id = *menza_ids().get(menza_name.as_str()).expect("unknown menza");

    let (rucak, vecera) = fetch(id).await;

    let mut lines = Vec::new();
    if !rucak.items.is_empty() {
        lines.push(("**=== Tablica 1 - Ručak ===**".to_string(), false));
        for (label, items) in rucak.items.iter() {
            lines.push((format!("**{label}**\n{}", items.iter().map(|n| format!("{} {n}", emojify(n))).collect::<Vec<_>>().join("\n")), true));
        }
    }
    if !vecera.items.is_empty() {
        lines.push(("**=== Tablica 2 - Večera ===**".to_string(), false));
        for (label, items) in vecera.items.iter() {
            lines.push((format!("**{label}**\n{}", items.iter().map(|n| format!("{} {n}", emojify(n))).collect::<Vec<_>>().join("\n")), true));
        }
    }

    Response::ReplyEmbed {
        title: "Menza".into(),
        description: format!("ID: *`{menza_name}`*"),
        color: 0x15D6EA,
        lines,
    }
}
use scraper::{Html, Selector};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::{funcs::router::{self, EmbedData, Request, Response}, route_handler, store, util};

const ERROR_COLOR: u32 = 0xEA2915;
const SUCCESS_COLOR: u32 = 0x6BEA15;
const ONEOFF_COLOR: u32 = 0x15D6EA;
const REPEATING_COLOR: u32 = 0x9415EA;

const ADMIN_ID: u64 = 213246013958258688;
const URL: &str = "https://riteh.uniri.hr/novosti/";
const SUB_KEY: &str = "riteh_novosti:sub";
const SEEN_KEY: &str = "riteh_novosti:seen";

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Novost {
    title: String,
    link: String,
    summary: String,
    category: String,
    img: Option<String>,
}

impl Novost {
    fn hash(&self) -> String {
        let mut h = Sha256::new();
        h.update(&self.link);
        h.update(&self.title);
        format!("{:x}", h.finalize())
    }
}

fn clean_text(s: &str) -> String {
    s.replace('\n', "")
        .replace('\t', "")
        .replace('\u{a0}', " ")
        .trim()
        .to_string()
}

fn parse_subs(val: &str) -> Vec<u64> {
    val.split(';').filter_map(|x| x.trim().parse().ok()).collect()
}

async fn get_subs() -> Vec<u64> {
    let s = store::store().lock().await;
    s.get(SUB_KEY).map(|v| parse_subs(&v)).unwrap_or_default()
}

async fn add_sub(channel_id: u64) {
    let mut subs = get_subs().await;
    if !subs.contains(&channel_id) {
        subs.push(channel_id);
    }
    let joined = subs.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(";");
    let s = store::store().lock().await;
    let _ = s.set(SUB_KEY, &joined);
}

async fn del_sub(channel_id: u64) {
    let subs = get_subs().await;
    let joined = subs.iter().filter(|&&x| x != channel_id).map(|x| x.to_string()).collect::<Vec<_>>().join(";");
    let s = store::store().lock().await;
    let _ = s.set(SUB_KEY, &joined);
}

async fn get_seen() -> Vec<String> {
    let s = store::store().lock().await;
    s.get(SEEN_KEY).map(|v| v.split(';').map(|x| x.to_string()).collect()).unwrap_or_default()
}

async fn add_seen(hash: &str) {
    let mut seen = get_seen().await;
    seen.push(hash.to_string());
    let joined = seen.join(";");
    let s = store::store().lock().await;
    let _ = s.set(SEEN_KEY, &joined);
}

async fn fetch_novosti() -> Vec<Novost> {
    let data_key = "data:riteh_novosti:data";
    let time_key = "data:riteh_novosti:time";
    {
        let s = store::store().lock().await;
        if let Ok(t) = s.get(time_key) {
            if let Ok(stored) = t.parse::<u64>() {
                if util::now_ms().saturating_sub(stored) < 60_000 {
                    if let Ok(val) = s.get(data_key) {
                        if let Ok(novosti) = serde_json::from_str::<Vec<Novost>>(&val) {
                            return novosti;
                        }
                    }
                }
            }
        }
    }

    let novosti = scrape().await.unwrap_or_default();

    let s = store::store().lock().await;
    if let Ok(json) = serde_json::to_string(&novosti) {
        let _ = s.set(data_key, &json);
        let _ = s.set(time_key, &util::now_ms().to_string());
    }

    novosti
}

async fn scrape() -> Result<Vec<Novost>, ()> {
    let body = reqwest::get(URL).await.map_err(|_| ())?.text().await.map_err(|_| ())?;
    let doc = Html::parse_document(&body);

    let container_sel = Selector::parse("div.elementor-loop-container.elementor-grid").map_err(|_| ())?;
    let post_sel = Selector::parse("div.post").map_err(|_| ())?;
    let title_sel = Selector::parse("div.elementor-widget-theme-post-title").map_err(|_| ())?;
    let excerpt_sel = Selector::parse("div.elementor-widget-theme-post-excerpt").map_err(|_| ())?;
    let p_sel = Selector::parse("p").map_err(|_| ())?;
    let a_sel = Selector::parse("a").map_err(|_| ())?;
    let img_sel = Selector::parse("img").map_err(|_| ())?;

    let container = doc.select(&container_sel).next().ok_or(())?;
    let mut novosti = Vec::new();
    for post in container.select(&post_sel) {
        let title = post
            .select(&title_sel)
            .next()
            .map(|e| clean_text(&e.text().collect::<String>()))
            .unwrap_or_default();
        let summary = post
            .select(&excerpt_sel)
            .next()
            .map(|e| clean_text(&e.text().collect::<String>()))
            .unwrap_or_default();
        let category = post
            .select(&p_sel)
            .next()
            .map(|e| clean_text(&e.text().collect::<String>()))
            .unwrap_or_default();
        let link = post
            .select(&a_sel)
            .next()
            .and_then(|e| e.value().attr("href"))
            .map(|s| s.trim().to_string())
            .unwrap_or_default();
        let img = post
            .select(&img_sel)
            .next()
            .and_then(|e| e.value().attr("src"))
            .map(|s| s.to_string())
            .filter(|s| {
                !s.contains("elementor-placeholder")
                    && !s.contains("uniri-logo-header")
                    && !s.contains("UNIRI_Logotip")
            });
        novosti.push(Novost { title, link, summary, category, img });
    }
    novosti.reverse();
    Ok(novosti)
}

fn novost_embed(n: &Novost, one_off: bool) -> EmbedData {
    EmbedData {
        title: n.title.clone(),
        description: format!("*{}*", n.category),
        color: if one_off { ONEOFF_COLOR } else { REPEATING_COLOR },
        lines: vec![(n.summary.clone(), false)],
        url: Some(n.link.clone()),
        image: n.img.clone(),
    }
}

async fn refresh(_r: Request) -> Vec<Response> {
    let novosti = fetch_novosti().await;

    let subs = get_subs().await;

    let mut out = Vec::new();
    let seen = get_seen().await;
    for n in &novosti {
        let h = n.hash();
        if seen.contains(&h) {
            continue;
        }
        let embed = novost_embed(n, false);
        for &ch in &subs {
            out.push(Response::SendEmbed { channel_id: ch, embed: embed.clone() });
        }
        add_seen(&h).await;
    }
    out
}

pub async fn init() {
    let mut r = router::router().write().await;
    r.register_command("novosti", route_handler!(novosti));
    r.register_command("novosti_sub", route_handler!(novosti_sub));
    r.register_command("novosti_unsub", route_handler!(novosti_unsub));
    r.register_command("dbg_refresh_novosti", route_handler!(dbg_refresh_novosti));
    r.register_periodic(route_handler!(refresh));
}

async fn novosti(r: Request) -> Vec<Response> {
    let (text, channel_id) = match r {
        Request::Message { text, channel_id, .. } => (text, channel_id),
        _ => return vec![],
    };
    let n: usize = match text.split_whitespace().nth(1).and_then(|s| s.parse().ok()) {
        Some(n) => n,
        None => {
            return vec![Response::ReplyEmbed(EmbedData {
                title: "Novosti".into(),
                description: "Koliko novosti? npr. `!novosti 5`".into(),
                color: ERROR_COLOR,
                lines: vec![],
                url: None,
                image: None,
            })];
        }
    };
    let novosti = fetch_novosti().await;
    let start = novosti.len().saturating_sub(n);
    novosti[start..]
        .iter()
        .map(|n| Response::SendEmbed { channel_id, embed: novost_embed(n, true) })
        .collect()
}

async fn novosti_sub(r: Request) -> Vec<Response> {
    let channel_id = match r {
        Request::Message { channel_id, .. } => channel_id,
        _ => return vec![],
    };
    if get_subs().await.contains(&channel_id) {
        return vec![Response::ReplyEmbed(EmbedData {
            title: "Greška!".into(),
            description: "Postoji pretplata novosti".into(),
            color: ERROR_COLOR,
            lines: vec![],
            url: None,
            image: None,
        })];
    }
    add_sub(channel_id).await;
    vec![Response::ReplyEmbed(EmbedData {
        title: "Uspjeh!".into(),
        description: "Pretplačeni na novosti".into(),
        color: SUCCESS_COLOR,
        lines: vec![],
        url: None,
        image: None,
    })]
}

async fn novosti_unsub(r: Request) -> Vec<Response> {
    let channel_id = match r {
        Request::Message { channel_id, .. } => channel_id,
        _ => return vec![],
    };
    del_sub(channel_id).await;
    vec![Response::ReplyEmbed(EmbedData {
        title: "Uspjeh!".into(),
        description: "Odjavljeni sa pretplane na novosti".into(),
        color: SUCCESS_COLOR,
        lines: vec![],
        url: None,
        image: None,
    })]
}

async fn dbg_refresh_novosti(r: Request) -> Vec<Response> {
    let user_id = match r {
        Request::Message { user_id, .. } => user_id,
        _ => return vec![],
    };
    if user_id != ADMIN_ID {
        return vec![];
    }
    let mut out = refresh(Request::None).await;
    let subs = get_subs().await;
    if let Some(last) = fetch_novosti().await.last() {
        let embed = novost_embed(last, true);
        for &ch in &subs {
            out.push(Response::SendEmbed { channel_id: ch, embed: embed.clone() });
        }
    }
    out
}

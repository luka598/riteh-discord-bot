use crate::{funcs::router::{self, Request, Response}, route_handler};

pub async fn ping(r: Request) -> Response {
    println!("{r:?}");

    Response::Reply { text: "pong".to_string() }
}

pub async fn init() {
    let mut r = router::router().write().await;
    r.register_command("ping", route_handler!(ping));
}

use crate::funcs::router::{self, Request, Response};
use crate::route_handler;

const ADMIN_ID: u64 = 213246013958258688;

pub async fn init() {
    let mut r = router::router().write().await;
    r.register_command("dbg_stop", route_handler!(dbg_stop));
}

async fn dbg_stop(r: Request) -> Vec<Response> {
    let user_id = match r {
        Request::Message { user_id, .. } => user_id,
        _ => return vec![],
    };
    if user_id != ADMIN_ID {
        return vec![];
    }
    println!("dbg_stop by admin {user_id}");
    std::process::exit(1);
}
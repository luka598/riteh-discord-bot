use std::collections::HashMap;
use std::future::Future;
use std::pin::Pin;

#[derive(Debug)]
pub enum Request {
    None,
    Message {text: String, user_id: u64, guild_id: Option<u64>, channel_id: u64},
}

#[derive(Debug)]
pub enum Response {
    None,
    Reply {text: String},
    ReplyEmbed {title: String, description: String, color: u32, lines: Vec<(String, bool)>},
}

pub type BoxFuture = Pin<Box<dyn Future<Output = Response> + Send>>;
pub type AsyncFn = Box<dyn Fn(Request) -> BoxFuture + Send + Sync>;

#[macro_export]
macro_rules! route_handler {
    ($f:expr) => {
        Box::new(move |x| -> $crate::funcs::router::BoxFuture {
            Box::pin($f(x))
        }) as $crate::funcs::router::AsyncFn
    };
}

pub struct Router {
    commands: HashMap<String, AsyncFn>,
}

impl Router {
    pub fn new() -> Self {
        Self { commands: HashMap::new() }
    }

    pub fn register_command(&mut self, command: &str, f: AsyncFn) {
        self.commands.insert(command.to_string(), f);
    }

    pub async fn run_command(&self, command: &str, arg: Request) -> Response {
        match self.commands.get(command) {
            Some(f) => f(arg).await,
            None => Response::None,
        }
    }

    pub async fn run_periodic(&self) -> Response {
        Response::None
    }
}

static GLOBAL_ROUTER: std::sync::OnceLock<tokio::sync::RwLock<Router>> = std::sync::OnceLock::new();

pub fn router() -> &'static tokio::sync::RwLock<Router> {
    GLOBAL_ROUTER.get_or_init(|| {
        tokio::sync::RwLock::new(Router::new())
    })
}

use std::collections::HashMap;
use std::future::Future;
use std::pin::Pin;

#[derive(Debug, Clone)]
pub struct EmbedData {
    pub title: String,
    pub description: String,
    pub color: u32,
    pub lines: Vec<(String, bool)>,
    pub url: Option<String>,
    pub image: Option<String>,
}

#[derive(Debug)]
pub enum Request {
    None,
    Message {text: String, user_id: u64, guild_id: Option<u64>, channel_id: u64},
}

#[derive(Debug)]
pub enum Response {
    None,
    Reply {text: String},
    ReplyEmbed(EmbedData),
    Send {channel_id: u64, text: String},
    SendEmbed {channel_id: u64, embed: EmbedData},
}

pub type BoxFuture = Pin<Box<dyn Future<Output = Vec<Response>> + Send>>;
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
    periodic: Vec<AsyncFn>,
}

impl Router {
    pub fn new() -> Self {
        Self { commands: HashMap::new(), periodic: Vec::new() }
    }

    pub fn register_command(&mut self, command: &str, f: AsyncFn) {
        self.commands.insert(command.to_string(), f);
    }

    pub fn register_periodic(&mut self, f: AsyncFn) {
        self.periodic.push(f);
    }

    pub async fn run_command(&self, command: &str, arg: Request) -> Vec<Response> {
        match self.commands.get(command) {
            Some(f) => f(arg).await,
            None => vec![],
        }
    }

    pub async fn run_periodic(&self) -> Vec<Response> {
        let mut out = Vec::new();
        for f in &self.periodic {
            out.extend(f(Request::None).await);
        }
        out
    }
}

static GLOBAL_ROUTER: std::sync::OnceLock<tokio::sync::RwLock<Router>> = std::sync::OnceLock::new();

pub fn router() -> &'static tokio::sync::RwLock<Router> {
    GLOBAL_ROUTER.get_or_init(|| {
        tokio::sync::RwLock::new(Router::new())
    })
}

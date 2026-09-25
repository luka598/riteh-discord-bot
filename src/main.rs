mod store;
mod funcs;
mod discord;
mod util;

#[tokio::main]
async fn main() {
    dotenvy::dotenv().unwrap();
    let discord_bot_token = std::env::var("DISCORD_BOT_TOKEN").unwrap();

    funcs::ping::init().await;
    funcs::scri_menza::init().await;

    discord::run(discord_bot_token).await;
}
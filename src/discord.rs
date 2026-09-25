use serenity::all::{CreateEmbed, CreateMessage};
use serenity::async_trait;
use serenity::model::channel::Message;
use serenity::prelude::*;

use crate::funcs::router;

struct Handler;

#[async_trait]
impl EventHandler for Handler {
    async fn ready(&self, ctx: Context, ready: serenity::all::Ready) {
        println!("{} is connected", ready.user.name);


    }

    async fn message(&self, ctx: Context, msg: Message) {
        let content = msg.content.to_string();

        if msg.content.starts_with("!") {
            let command: String = content
                .strip_prefix('!')
                .and_then(|s| s.split_once(' '))
                .map(|(cmd, _rest)| cmd)
                .unwrap_or_else(|| content.strip_prefix('!').unwrap_or(&content))
                .to_string();

            let r = router::router().read().await;
            let resp = r
                .run_command(
                    &command,
                    router::Request::Message {
                        text: content,
                        user_id: msg.author.id.into(),
                        guild_id: msg.guild_id.map(|x| x.into()),
                        channel_id: msg.channel_id.into(),
                    },
                )
                .await;

            match resp {
                router::Response::None => {}
                router::Response::Reply { text } => {
                    let builder = CreateMessage::new().content(text).reference_message(&msg);
                    if let Err(why) = msg.channel_id.send_message(&ctx.http, builder).await {
                        println!("Error sending message: {why:?}");
                    }
                }
                router::Response::ReplyEmbed { title, description, color, lines } => {
                    let mut embed = CreateEmbed::new().title(title).description(description).colour(color);

                    for (line, inline) in lines {
                        embed = embed.field("", line, inline);
                    }

                    let builder = CreateMessage::new().embed(embed).reference_message(&msg);
                    if let Err(why) = msg.channel_id.send_message(&ctx.http, builder).await {
                        println!("Error sending message: {why:?}");
                    }
                }
            }
        }
    }
}

pub async fn run(token: String) {
    let intents = GatewayIntents::GUILD_MESSAGES | GatewayIntents::DIRECT_MESSAGES | GatewayIntents::MESSAGE_CONTENT;

    let mut client = Client::builder(&token, intents).event_handler(Handler).await.expect("Err creating client");

    if let Err(why) = client.start().await {
        println!("Client error: {why:?}");
    }
}

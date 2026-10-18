use serenity::all::{CreateEmbed, CreateMessage};
use serenity::async_trait;
use serenity::model::channel::Message;
use serenity::prelude::*;

use crate::funcs::router::{self, EmbedData, Response};

struct Handler;

fn build_embed(d: &EmbedData) -> CreateEmbed {
    let mut embed = CreateEmbed::new().title(&d.title).description(&d.description).colour(d.color);
    if let Some(u) = &d.url {
        embed = embed.url(u);
    }
    if let Some(img) = &d.image {
        embed = embed.image(img);
    }
    for (line, inline) in &d.lines {
        embed = embed.field("", line, *inline);
    }
    embed
}

async fn send_response(http: &serenity::http::Http, resp: Response, message_ref: Option<&Message>) {
    match resp {
        Response::None => {}
        Response::Reply { text } => {
            let m = message_ref.expect("Reply requires message context");
            let builder = CreateMessage::new().content(text).reference_message(m);
            if let Err(why) = m.channel_id.send_message(http, builder).await {
                println!("Error sending message: {why:?}");
            }
        }
        Response::ReplyEmbed(d) => {
            let m = message_ref.expect("Reply requires message context");
            let builder = CreateMessage::new().embed(build_embed(&d)).reference_message(m);
            if let Err(why) = m.channel_id.send_message(http, builder).await {
                println!("Error sending message: {why:?}");
            }
        }
        Response::Send { channel_id, text } => {
            let builder = CreateMessage::new().content(text);
            if let Err(why) = serenity::all::ChannelId::new(channel_id).send_message(http, builder).await {
                println!("Error sending message: {why:?}");
            }
        }
        Response::SendEmbed { channel_id, embed } => {
            let builder = CreateMessage::new().embed(build_embed(&embed));
            if let Err(why) = serenity::all::ChannelId::new(channel_id).send_message(http, builder).await {
                println!("Error sending message: {why:?}");
            }
        }
    }
}

#[async_trait]
impl EventHandler for Handler {
    async fn ready(&self, ctx: Context, ready: serenity::all::Ready) {
        println!("{} is connected", ready.user.name);

        let http = ctx.http.clone();
        tokio::spawn(async move {
            loop {
                let outs = {
                    let r = router::router().read().await;
                    r.run_periodic().await
                };
                for resp in outs {
                    send_response(&http, resp, None).await;
                }
                tokio::time::sleep(std::time::Duration::from_secs(3600)).await;
            }
        });
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
            let resps = r
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

            for resp in resps {
                send_response(&ctx.http, resp, Some(&msg)).await;
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

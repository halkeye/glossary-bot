import json
import os
import logging
import re

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.authorization import AuthorizeResult
from slack_sdk.web.client import WebClient

from gloss.bot import Bot

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

database_url = os.environ["DATABASE_URL"]
# SQLAlchemy no longer recognizes postgres:// URLs as "postgresql"
# https://github.com/sqlalchemy/sqlalchemy/issues/6083
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)


def authorize(enterprise_id, team_id, user_id, client: WebClient, logger):
    logger.info(f"enterprise_id={enterprise_id},team_id={team_id},user_id={user_id}")
    # You can implement your own logic here
    token = os.environ["SLACK_BOT_TOKEN"]
    return AuthorizeResult.from_auth_test_response(
        auth_test_response=client.auth_test(token=token),
        bot_token=token,
    )


app = App(
    logger=logger,
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    installation_store=None,
    authorize=authorize,
)

engine = create_engine(database_url, echo=False, pool_recycle=3600)


@app.command(os.getenv("SLASH_COMMAND", "/glossary"))
def glossary_command(ack, respond, body):
    """
    values posted by Slack:
        token: the authenticaton token from Slack; available in the integration settings.
        team_domain: the name of the team (i.e. what shows up in the URL: {xxx}.slack.com)
        team_id: unique ID for the team
        channel_name: the name of the channel the message was sent from
        channel_id: unique ID for the channel the message was sent from
        user_name: the name of the user that sent the message
        user_id: unique ID for the user that sent the message
        command: the command that was used to generate the request (like '/gloss')
        text: the text that was sent along with the command (like everything after '/gloss ')
    """
    try:
        logger.debug(body)
        with Session(engine) as session:
            bot = Bot(bot_name="Glossary Bot", session=session)
            ack()
            respond(
                bot.handle_glossary(
                    user_name=body["user_name"],
                    slash_command=body["command"],
                    text=body["text"],
                )
            )
    except Exception as e:
        respond(f"An exception happened: {e}")
        raise


@app.event("app_mention")
def glossary_mention(client, event, say):
    try:
        logger.info(event)
        result = re.search(r"^\s*\<\@([a-zA-Z0-9]*)\>\s*(.*)", event["text"])
        if result is None:
            return

        bot_info = client.users_info(user=result.group(1))
        if not bot_info["ok"]:
            raise RuntimeError("Unable to look up bot")
        user_info = client.users_info(user=event["user"])
        if not user_info["ok"]:
            raise RuntimeError("Unable to look up user")

        with Session(engine) as session:
            bot = Bot(bot_name="Glossary Bot", session=session)
            response = bot.handle_glossary(
                user_name=user_info["user"]["name"],
                slash_command=f"@{bot_info['user']['name']}",
                text=result.group(2),
            )
            print(json.dumps(response))
            say(response, thread_ts=event.get("thread_ts"))
    except Exception as e:
        say(f"An exception happened: {e}")
        raise


if __name__ == "__main__":
    # export SLACK_APP_TOKEN=xapp-***
    # export SLACK_BOT_TOKEN=xoxb-***
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()

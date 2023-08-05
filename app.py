import json
import os
import logging
import re
from functools import partial

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.authorization import AuthorizeResult
from slack_sdk.web.client import WebClient

from gloss.views import STATS_CMDS, RECENT_CMDS, HELP_CMDS, SET_CMDS, DELETE_CMDS, SEARCH_CMDS, Bot

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

database_url = os.environ["DATABASE_URL"]

def authorize(enterprise_id, team_id, user_id, client: WebClient, logger):
    logger.info(f"{enterprise_id},{team_id},{user_id}")
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

engine = create_engine(database_url, echo=False)

def handle_glossary(respond, body):
    '''
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
    '''

    try:
        #with engine.connect() as conn:
        with Session(engine) as session:
            # get the user name and channel ID
            user_name = body['user_name']
            slash_command = body['command']

            # strip excess spaces from the text
            full_text = body['text'].strip()
            full_text = re.sub(" +", " ", full_text)
            command_text = full_text

            bot = Bot(bot_name="Glossary Bot", session=session, user_name=body['user_name'], slash_command=body['command'], text=body['text'])

            #
            # GET definition (for a single word that can't be interpreted as a command)
            #

            # if the text is a single word that's not a single-word command, treat it as a get
            if command_text.count(" ") == 0 and len(command_text) > 0 and \
            command_text.lower() not in STATS_CMDS + RECENT_CMDS + HELP_CMDS + SET_CMDS:
                return respond(bot.query_definition_and_get_response(slash_command, command_text, user_name))

            #
            # SET definition
            #

            # if the text contains an '=', treat it as a 'set' command
            if '=' in command_text:
                return respond(bot.set_definition_and_get_response(slash_command, command_text, user_name))

            # we'll respond privately if the text is prefixed with 'shh ' (or any number of s followed by any number of h)
            shh_pattern = re.compile(r'^s+h+ ')
            private_response = shh_pattern.match(command_text)
            if private_response:
                # strip the 'shh' from the command text
                command_text = shh_pattern.sub('', command_text)

            # extract the command action and parameters
            command_action, command_params = bot.get_command_action_and_params(command_text)

            #
            # DELETE definition
            #

            if command_action in DELETE_CMDS:
                delete_term = command_params

                # verify that the definition is in the database
                entry = bot.query_definition(delete_term)
                if not entry:
                    return respond("Sorry, but *{bot_name}* has no definition for {term}".format(bot_name=BOT_NAME, term=make_bold(delete_term)))

                # delete the definition from the database
                try:
                    session.delete(entry)
                    session.commit()
                except Exception as e:
                    return respond("Sorry, but *{bot_name}* was unable to delete that definition: {message}, {args}".format(bot_name=BOT_NAME, message=e.message, args=e.args))

                return respond("*{bot_name}* has deleted the definition for {term}, which was {definition}".format(bot_name=BOT_NAME, term=make_bold(delete_term), definition=make_bold(entry.definition)))

            #
            # SEARCH for a string
            #

            if command_action in SEARCH_CMDS:
                search_term = command_params

                return respond(bot.search_term_and_get_response(search_term))

            #
            # HELP
            #

            if command_action in HELP_CMDS or command_text.strip() == "":
                return respond("*{command} _term_* to show the definition for a term\n*{command} _term_ = _definition_* to set the definition for a term\n*{command} _alias_ = see _term_* to set an alias for a term\n*{command} delete _term_* to delete the definition for a term\n*{command} stats* to show usage statistics\n*{command} recent* to show recently defined terms\n*{command} search _term_* to search terms and definitions\n*{command} shh _command_* to get a private response\n*{command} help* to see this message\n<https://github.com/codeforamerica/glossary-bot/issues|report bugs and request features>".format(command=slash_command))

            #
            # STATS
            #

            if command_action in STATS_CMDS:
                stats_newline = bot.get_stats()
                stats_comma = re.sub("\n", ", ", stats_newline)
                if not private_response:
                    # send the message
                    fallback = "{name} {command} stats: {comma}".format(name=user_name, command=slash_command, comma=stats_comma)
                    pretext = "*{name}* {command} stats".format(name=user_name, command=slash_command)
                    title = ""
                    send_webhook_with_attachment(channel_id=channel_id, text=stats_newline, fallback=fallback, pretext=pretext, title=title)
                    return "", 200

                else:
                    return respond(stats_comma)

            #
            # LEARNINGS/RECENT
            #

            if command_action in RECENT_CMDS:
                # extract parameters
                recent_args = bot.parse_learnings_params(command_params)
                learnings_plain_text, learnings_rich_text = bot.get_learnings(**recent_args)
                if not private_response:
                    # send the message
                    fallback = "{name} {command} {action} {params}: {text}".format(name=user_name, command=slash_command, action=command_action, params=command_params, text=learnings_plain_text)
                    pretext = "*{name}* {command} {action} {params}".format(name=user_name, command=slash_command, action=command_action, params=command_params)
                    title = ""
                    send_webhook_with_attachment(channel_id=channel_id, text=learnings_rich_text, fallback=fallback, pretext=pretext, title=title, mrkdwn_in=["text"])
                    return

                else:
                    return respond(learnings_plain_text)

            #
            # GET definition (for any text that wasn't caught before this)
            #

            # check the definition
            if private_response:
                return respond(bot.query_definition_and_get_response(slash_command, command_text, user_name))
            else:
                return respond(bot.query_definition_and_get_response(slash_command, command_text, user_name))
    except Exception as e:
        respond(f"An exception happened: {e}")
        raise

@app.command("/glossary")
def glossary_command(ack, respond, body):
    logger.info(body)
    with Session(engine) as session:
        bot = Bot(bot_name="Glossary Bot", session=session)
        ack()
        bot.handle_glossary(respond=respond, user_name=body['user_name'], slash_command=body['command'], text=body['text'])

@app.event("app_mention")
def glossary_mention(client, event, say):
    logger.info(event)
    result = re.search(r"^\s*\<\@([a-zA-Z0-9]*)\>\s*(.*)", event["text"])
    if result is None:
        return

    bot = client.users_info(user=result.group(1))
    if bot['ok'] != True:
        raise RuntimeError("Unable to look up bot")
    user = client.users_info(user=event['user'])
    if user['ok'] != True:
        raise RuntimeError("Unable to look up user")

    logger.info(user)
    event['user_name'] = user['user']['name']
    event['channel_id'] = event["channel"]
    event['command'] = f"@{bot['user']['name']}"
    event['text'] = result.group(2)

    handle_glossary(partial(say, thread_ts=event.get("thread_ts")), event)

if __name__ == "__main__":
    # export SLACK_APP_TOKEN=xapp-***
    # export SLACK_BOT_TOKEN=xoxb-***
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
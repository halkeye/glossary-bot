import random
import re
import logging
from thefuzz import process
from .models import Definition, Interaction
from sqlalchemy import func, distinct, sql
from datetime import datetime

STATS_CMDS = ("stats",)
RECENT_CMDS = ("learnings", "recent")
HELP_CMDS = ("help", "?")
SET_CMDS = ("=",)
DELETE_CMDS = ("delete",)
SEARCH_CMDS = ("search",)

ALIAS_KEYWORDS = ("see also", "see")

MAX_CONFIDENCE = 50

BOT_EMOJI = ":lipstick:"

logger = logging.getLogger(__name__)


def get_image_url(text):
    ''' Extract an image url from the passed text. If there are multiple image urls,
        only the first one will be returned.
    '''
    if 'http' not in text:
        return None

    for chunk in text.split(' '):
        if verify_image_url(text) and verify_url(text):
            return chunk

    return None

def make_bold(text):
    ''' make the passed text bold, accounting for newlines
    '''
    newline_split = text.split("\n")
    bold_split = []
    for line in newline_split:
        bold_line = line
        if line.strip() != "":
            bold_line = "*{}*".format(line.strip())
        bold_split.append(bold_line)

    return "\n".join(bold_split)

def verify_url(text):
    ''' verify that the passed text is a URL

        Adapted from @adamrofer's Python port of @dperini's pattern here: https://gist.github.com/dperini/729294
    '''
    url_pattern = re.compile("^(?:(?:https?)://|)(?:(?!(?:10|127)(?:\.\d{1,3}){3})(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)(?:\.(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)*(?:\.(?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)))(?::\d{2,5})?(?:/\S*)?$", re.UNICODE)
    return url_pattern.match(text)

def verify_image_url(text):
    ''' Verify that the passed text is an image URL.

        We're verifying image URLs for inclusion in Slack's Incoming Webhook integration, which
        requires a scheme at the beginning (http(s)) and a file extention at the end to render
        correctly. So, a URL which passes verify_url() (like example.com/kitten.gif) might not
        pass this test. If you need to test that the URL is both valid AND an image suitable for
        the Incoming Webhook integration, run it through both verify_url() and verify_image_url().
    '''
    return (re.match('http', text) and re.search(r'[gif|jpg|jpeg|png|bmp]$', text))


def parse_learnings_params(command_params):
    ''' Parse the passed learnings command params
    '''
    recent_args = {}
    # extract parameters
    params_list = command_params.split(' ')
    for param in params_list:
        if param == "random":
            recent_args['sort_order'] = param
            continue
        if param == "alpha" or param == "alphabetical":
            recent_args['sort_order'] = "alpha"
            continue
        if param == "all":
            recent_args['how_many'] = 0
            continue
        try:
            passed_int = int(param)
            if 'how_many' not in recent_args:
                recent_args['how_many'] = passed_int
            elif 'offset' not in recent_args:
                recent_args['offset'] = passed_int
        except ValueError:
            continue

    return recent_args

def get_command_action_and_params(command_text):
    ''' Parse the passed string for a command action and parameters
    '''
    command_components = command_text.split(' ')
    command_action = command_components[0].lower()
    command_params = " ".join(command_components[1:])
    return command_action, command_params

def check_definition_for_alias(definition):
    ''' If the passed definition starts with a keyword in ALIAS_KEYWORDS, strip
        that prefix from the definition and return it.
    '''
    for keyword in ALIAS_KEYWORDS:
        if definition.lower().startswith(keyword):
            return re.split(keyword, definition, flags=re.IGNORECASE)[1].strip()

    return None

class Bot:
    def __init__(self, session, bot_name):
        self.session = session
        self.bot_name = bot_name

    def get_payload_values(self, channel_id="", text=None):
        ''' Get a dict describing a standard webhook
        '''
        payload_values = {}
        payload_values['channel'] = channel_id
        payload_values['text'] = text
        payload_values['username'] = self.bot_name
        payload_values['icon_emoji'] = BOT_EMOJI
        return payload_values

    def get_stats(self):
        ''' Gather and return some statistics
        '''
        entries = self.session.query(func.count(Definition.term)).scalar()
        definers = self.session.query(func.count(distinct(Definition.user_name))).scalar()
        queries = self.session.query(func.count(Interaction.action)).scalar()
        outputs = (
            ("I have definitions for", entries, "term", "terms", "I don't have any definitions"),
            ("", definers, "person has defined terms", "people have defined terms", "Nobody has defined terms"),
            ("I've been asked for definitions", queries, "time", "times", "Nobody has asked me for definitions")
        )
        lines = []
        for prefix, period, singular, plural, empty_line in outputs:
            if period:
                lines.append("{}{} {}".format("{} ".format(prefix) if prefix else "", period, singular if period == 1 else plural))
            else:
                lines.append(empty_line)
        # return the message
        return "\n".join(lines)

    def get_learnings(self, how_many=12, sort_order="recent", offset=0):
        ''' Gather and return some recent definitions
        '''
        order_descending = Definition.creation_date.desc()
        order_random = func.random()
        order_alphabetical = Definition.term
        order_function = order_descending
        prefix_singluar = "I recently learned the definition for"
        prefix_plural = "I recently learned definitions for"
        no_definitions_text = "I haven't learned any definitions yet."
        if sort_order == "random":
            order_function = order_random
        elif sort_order == "alpha":
            order_function = order_alphabetical

        if sort_order == "random" or sort_order == "alpha" or offset > 0:
            prefix_singluar = "I know the definition for"
            prefix_plural = "I know definitions for"

        # if how_many is 0, ignore offset and return all results
        if how_many == 0:
            definitions = self.session.query(Definition).order_by(order_function).all()
        # if order is random and there is an offset, randomize the results after the query
        elif sort_order == "random" and offset > 0:
            definitions = self.session.query(Definition).order_by(order_descending).limit(how_many).offset(offset).all()
            random.shuffle(definitions)
        else:
            definitions = self.session.query(Definition).order_by(order_function).limit(how_many).offset(offset).all()

        if not definitions:
            return no_definitions_text, no_definitions_text

        wording = prefix_plural if len(definitions) > 1 else prefix_singluar
        plain_text = "{}: {}".format(wording, ', '.join([item.term for item in definitions]))
        rich_text = "{}: {}".format(wording, ', '.join([make_bold(item.term) for item in definitions]))
        return plain_text, rich_text

    def log_query(self, term, user_name, action):
        ''' Log a query into the interactions table
        '''
        try:
            self.session.add(Interaction(term=term, user_name=user_name, action=action))
            self.session.commit()
        except Exception:
            pass

    def query_definition(self, term):
        ''' Query the definition for a term from the database
        '''
        return self.session.query(Definition).filter(func.lower(Definition.term) == func.lower(term)).first()

    def get_matches_for_term(self, term):
        ''' Search the glossary for entries that are matches for the passed term.
        '''

        # strip pattern-matching metacharacters from the term
        stripped_term = re.sub(r'\||_|%|\*|\+|\?|\{|\}|\(|\)|\[|\]', '', term)
        # get ILIKE matches for the term
        # in SQL: SELECT term FROM definitions WHERE term ILIKE '%{}%'.format(stripped_term);
        like_matches = self.session.query(Definition).filter(Definition.term.ilike(f"%{stripped_term}%")).order_by(Definition.term.desc())
        like_results = [entry.term for entry in like_matches]

        all_rows = {row.term:row.definition for row in self.session.query(Definition).order_by(Definition.term.asc()).all()}
        fuzzy_results = [result[2] for result in sorted(filter(lambda result: result[1] >= MAX_CONFIDENCE, process.extract(term, all_rows, limit=20)), key=lambda result: result[1])]

        results = list(fuzzy_results)
        for check_term in like_results:
            if check_term not in results:
                results.insert(0, check_term)

        return results

    def query_definition_and_get_response(self, slash_command, command_text, user_name):
        ''' Get the definition for the passed term and return the appropriate responses
        '''
        # query the definition
        entry = self.query_definition(command_text)
        if not entry:
            # remember this query
            self.log_query(term=command_text, user_name=user_name, action="not_found")

            message = f"Sorry, there is no definition for *{command_text}*. You can set a definition with the command *{slash_command} {command_text} = _definition_*"

            search_results = self.get_matches_for_term(command_text)
            if len(search_results):
                search_results_styled = ', '.join([make_bold(term) for term in search_results])
                message = f"{message}, or try asking for one of these terms that may be related: {search_results_styled}"

            return message

        # remember this query
        self.log_query(term=command_text, user_name=user_name, action="found")

        # if the definition starts with an alias keyphrase, check to see if the rest
        # of the definition matches another entry, and return that definition instead
        alias_term = check_definition_for_alias(entry.definition)
        if alias_term:
            alias_entry = self.query_definition(alias_term)

            if alias_entry:
                entry = alias_entry

        image_url = get_image_url(entry.definition)

        returnVal = f"{make_bold(entry.term)}: {entry.definition}"
        if image_url is not None:
            return {
                "text": returnVal,
                "blocks": [
                    {"type": "section", "text": { "type": "mrkdwn", "text": returnVal } },
                    { "type": "image", "image_url": image_url, "alt_text": returnVal }
                ]
            }

        return returnVal

    def search_term_and_get_response(self, command_text):
        ''' Search the database for the passed term and return the results
        '''
        # query the definition
        search_results = self.get_matches_for_term(command_text)
        if len(search_results):
            search_results_styled = ', '.join([make_bold(term) for term in search_results])
            message = f"{self.bot_name} found {make_bold(command_text)} in: {search_results_styled}"
        else:
            message = f"{self.bot_name} could not find {make_bold(command_text)} in any terms or definitions."

        return message

    def set_definition_and_get_response(self, slash_command, command_params, user_name):
        ''' Set the definition for the passed parameters and return the approriate responses
        '''
        set_components = command_params.split('=', 1)
        set_term = set_components[0].strip()
        set_value = set_components[1].strip() if len(set_components) > 1 else ""

        # reject poorly formed set commands
        if "=" not in command_params or not set_term or not set_value:
            return f"Sorry, but *{self.bot_name}* didn't understand your command. You can set definitions like this: *{slash_command} EW = Eligibility Worker*"

        # reject attempts to set reserved terms
        if set_term.lower() in STATS_CMDS + RECENT_CMDS + HELP_CMDS:
            return f"Sorry, but *{self.bot_name}* can't set a definition for {make_bold(set_term)} because it's a reserved term."

        # check the database to see if the term's already defined
        entry = self.query_definition(set_term)
        if entry:
            if set_term != entry.term or set_value != entry.definition:
                # update the definition in the database
                last_term = entry.term
                last_value = entry.definition
                entry.term = set_term
                entry.definition = set_value
                entry.user_name = user_name
                entry.creation_date = datetime.utcnow()

                self.session.add(entry)
                self.session.commit()

                return f"The definition for {make_bold(set_term)} is now set to {make_bold(set_value)}, overwriting the previous entry, which was {make_bold(last_term)} defined as {make_bold(last_value)}"
            else:
                return f"The definition for {make_bold(set_term)} was already set to {make_bold(set_value)}"

        # save the definition in the database
        entry = Definition(term=set_term, definition=set_value, user_name=user_name)
        self.session.add(entry)
        self.session.commit()

        return f"Definition for {make_bold(set_term)} is now set to {make_bold(set_value)}"

    def handle_glossary(self, user_name, slash_command, text):
        full_text = text.strip()
        full_text = re.sub(" +", " ", full_text)
        command_text = full_text

        #
        # GET definition (for a single word that can't be interpreted as a command)
        #

        # if the text is a single word that's not a single-word command, treat it as a get
        if command_text.count(" ") == 0 and len(command_text) > 0 and \
        command_text.lower() not in STATS_CMDS + RECENT_CMDS + HELP_CMDS + SET_CMDS:
            return self.query_definition_and_get_response(slash_command, command_text, user_name)

        #
        # SET definition
        #

        # if the text contains an '=', treat it as a 'set' command
        if '=' in command_text:
            return self.set_definition_and_get_response(slash_command, command_text, user_name)

        # extract the command action and parameters
        command_action, command_params = get_command_action_and_params(command_text)

        #
        # DELETE definition
        #

        if command_action in DELETE_CMDS:
            delete_term = command_params

            # verify that the definition is in the database
            entry = self.query_definition(delete_term)
            if not entry:
                return f"Sorry, but *{self.bot_name}* has no definition for {make_bold(delete_term)}"

            # delete the definition from the database
            try:
                self.session.delete(entry)
                self.session.commit()
            except Exception as e:
                return f"Sorry, but *{self.bot_name}* was unable to delete that definition: {e.message}, {e.args}"

            return f"*{self.bot_name}* has deleted the definition for {make_bold(delete_term)}, which was {make_bold(entry.definition)}"

        #
        # SEARCH for a string
        #

        if command_action in SEARCH_CMDS:
            search_term = command_params

            return self.search_term_and_get_response(search_term)

        #
        # HELP
        #

        if command_action in HELP_CMDS or command_text.strip() == "":
            return f"*{slash_command} _term_* to show the definition for a term\n*{slash_command} _term_ = _definition_* to set the definition for a term\n*{slash_command} _alias_ = see _term_* to set an alias for a term\n*{slash_command} delete _term_* to delete the definition for a term\n*{slash_command} stats* to show usage statistics\n*{slash_command} recent* to show recently defined terms\n*{slash_command} search _term_* to search terms and definitions\n*{slash_command} help* to see this message\n<https://github.com/codeforamerica/glossary-bot/issues|report bugs and request features>"

        #
        # STATS
        #

        if command_action in STATS_CMDS:
            stats_newline = self.get_stats()
            return stats_newline

        #
        # LEARNINGS/RECENT
        #

        if command_action in RECENT_CMDS:
            # extract parameters
            recent_args = parse_learnings_params(command_params)
            learnings_plain_text, learnings_rich_text = self.get_learnings(**recent_args)
            return learnings_rich_text

        #
        # GET definition (for any text that wasn't caught before this)
        #

        # check the definition
        return self.query_definition_and_get_response(slash_command, command_text, user_name)
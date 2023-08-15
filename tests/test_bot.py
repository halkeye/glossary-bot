#!/usr/bin/env python
# -*- coding: utf8 -*-
import json
import pytest

from . import conftest  # noqa: F401

from gloss.models import Definition, Interaction

class TestBot:
    def test_set_definition(self, db_session, handle_glossary):
        ''' A definition set via a POST is recorded in the database
        '''
        robo_response = handle_glossary(text="EW = Eligibility Worker")
        assert robo_response == 'Definition for *EW* is now set to *Eligibility Worker*'

        filter = Definition.term == "EW"
        definition_check = db_session.query(Definition).filter(filter).first()
        assert definition_check is not None
        assert definition_check.term == "EW"
        assert definition_check.definition == "Eligibility Worker"

    def test_set_definition_with_lots_of_whitespace(self, db_session, handle_glossary):
        ''' Excess whitespace is trimmed when parsing the set command.
        '''
        robo_response = handle_glossary(text="     EW   =    Eligibility      Worker  ")
        assert robo_response == 'Definition for *EW* is now set to *Eligibility Worker*'

        filter = Definition.term == "EW"
        definition_check = db_session.query(Definition).filter(filter).first()
        assert definition_check is not None
        assert definition_check.term == "EW"
        assert definition_check.definition == "Eligibility Worker"

    def test_set_definition_with_multiple_equals_signs(self, db_session, handle_glossary):
        ''' A set with multiple equals signs considers all equals signs after
            the first to be part of the definition
        '''
        robo_response = handle_glossary(text="EW = Eligibility Worker = Cool Person=Yeah")
        assert robo_response == 'Definition for *EW* is now set to *Eligibility Worker = Cool Person=Yeah*'

        filter = Definition.term == "EW"
        definition_check = db_session.query(Definition).filter(filter).first()
        assert definition_check is not None
        assert definition_check.term == "EW"
        assert definition_check.definition == "Eligibility Worker = Cool Person=Yeah"

    def test_reset_definition(self, db_session, handle_glossary):
        ''' Setting a definition for an existing term overwrites the original
        '''
        robo_response = handle_glossary(text="EW = Eligibility Worker")
        assert robo_response == 'Definition for *EW* is now set to *Eligibility Worker*'

        filter = Definition.term == "EW"
        definition_check = db_session.query(Definition).filter(filter).first()
        assert definition_check is not None
        assert definition_check.term == "EW"
        assert definition_check.definition == "Eligibility Worker"

        robo_response = handle_glossary(text="EW = Egg Weathervane")
        assert robo_response == 'The definition for *EW* is now set to *Egg Weathervane*, overwriting the previous entry, which was *EW* defined as *Eligibility Worker*'

        filter = Definition.term == "EW"
        definition_check = db_session.query(Definition).filter(filter).first()
        assert definition_check is not None
        assert definition_check.term == "EW"
        assert definition_check.definition == "Egg Weathervane"

    def test_set_same_word_with_different_capitalization(self, db_session, handle_glossary):
        ''' We can't set different definitions for the same word by using different cases
        '''
        robo_response = handle_glossary(text="lower case = NOT UPPER CASE")
        assert "Definition for *lower case* is now set to *NOT UPPER CASE*" == robo_response

        filter = Definition.term == "lower case"
        definition_check = db_session.query(Definition).filter(filter).first()
        assert definition_check is not None
        assert definition_check.term == "lower case"
        assert definition_check.definition == "NOT UPPER CASE"

        robo_response = handle_glossary(text="LOWER CASE = really not upper case")
        assert "overwriting the previous entry" in json.dumps(robo_response)

        robo_response = handle_glossary(text="lower case")
        assert "*LOWER CASE*: really not upper case" == robo_response

    def test_set_identical_definition(self, db_session, handle_glossary):
        ''' Correct response for setting an identical definition for an existing term
        '''
        robo_response = handle_glossary(text="EW = Eligibility Worker")
        assert "Definition for *EW* is now set to *Eligibility Worker*" == robo_response

        filter = Definition.term == "EW"
        definition_check = db_session.query(Definition).filter(filter).first()
        assert definition_check is not None
        assert definition_check.term == "EW"
        assert definition_check.definition == "Eligibility Worker"

        robo_response = handle_glossary(text="EW = Eligibility Worker")
        assert "The definition for *EW* was already set to *Eligibility Worker*" == robo_response

    def test_set_command_word_definitions(self, db_session, handle_glossary):
        ''' We can successfully set definitions for unreserved command words.
        '''
        robo_response = handle_glossary(text="SHH = Sonic Hedge Hog")
        assert "Definition for *SHH* is now set to *Sonic Hedge Hog*" == robo_response

        filter = Definition.term == "SHH"
        definition_check = db_session.query(Definition).filter(filter).first()
        assert definition_check is not None
        assert definition_check.term == "SHH"
        assert definition_check.definition == "Sonic Hedge Hog"

        robo_response = handle_glossary(text="SSH = Secure SHell")
        assert "Definition for *SSH* is now set to *Secure SHell*" == robo_response

        filter = Definition.term == "SSH"
        definition_check = db_session.query(Definition).filter(filter).first()
        assert definition_check is not None
        assert definition_check.term == "SSH"
        assert definition_check.definition == "Secure SHell"

        robo_response = handle_glossary(text="Delete = Remove or Obliterate")
        assert "Definition for *Delete* is now set to *Remove or Obliterate*" == robo_response

        filter = Definition.term == "Delete"
        definition_check = db_session.query(Definition).filter(filter).first()
        assert definition_check is not None
        assert definition_check.term == "Delete"
        assert definition_check.definition == "Remove or Obliterate"

        robo_response = handle_glossary(text="help me = I'm in hell")
        assert "Definition for *help me* is now set to *I\'m in hell*" == robo_response

        filter = Definition.term == "help me"
        definition_check = db_session.query(Definition).filter(filter).first()
        assert definition_check is not None
        assert definition_check.term == "help me"
        assert definition_check.definition == "I'm in hell"

    def test_failed_set_command_word_definitions(self, db_session, handle_glossary):
        ''' We can't successfully set definitions for reserved command words.
        '''
        robo_response = handle_glossary(text="Stats = Statistics")
        assert "because it's a reserved term" in json.dumps(robo_response)

        robo_response = handle_glossary(text="help = aid")
        assert "because it's a reserved term" in json.dumps(robo_response)

        robo_response = handle_glossary(text="LeArNiNgS = recently")
        assert "because it's a reserved term" in json.dumps(robo_response)

        robo_response = handle_glossary(text="? = riddle me this")
        assert "because it's a reserved term" in json.dumps(robo_response)

    def test_get_definition(self, db_session, handle_glossary):
        ''' We can succesfully set and get a definition from the bot
        '''
        # set & test a definition
        handle_glossary(text="EW = Eligibility Worker")

        filter = Definition.term == "EW"
        definition_check = db_session.query(Definition).filter(filter).first()
        assert definition_check is not None
        assert definition_check.term == "EW"
        assert definition_check.definition == "Eligibility Worker"

        robo_response = handle_glossary(text="EW")
        assert '*EW*: Eligibility Worker' == robo_response

        # the request was recorded in the interactions table
        interaction_check = db_session.query(Interaction).first()
        assert interaction_check is not None
        assert interaction_check.user_name == "testuser"
        assert interaction_check.term == "EW"
        assert interaction_check.action == "found"

    def test_get_definition_with_special_characters(self, db_session, handle_glossary):
        ''' We can succesfully set and get a definition with special characters from the bot
        '''
        # set & test a definition
        handle_glossary(text="EW = ™¥∑ø∂∆∫")

        filter = Definition.term == "EW"
        definition_check = db_session.query(Definition).filter(filter).first()
        assert definition_check is not None
        assert definition_check.term == "EW"
        assert definition_check.definition == "™¥∑ø∂∆∫"

        robo_response = handle_glossary(text="EW")
        assert '*EW*: ™¥∑ø∂∆∫' == robo_response

        # the request was recorded in the interactions table
        interaction_check = db_session.query(Interaction).first()
        assert interaction_check is not None
        assert interaction_check.user_name == "testuser"
        assert interaction_check.term == "EW"
        assert interaction_check.action == "found"

    def test_request_nonexistent_definition(self, db_session, handle_glossary):
        ''' Test requesting a non-existent definition
        '''
        # send a POST to the bot to request the definition
        robo_response = handle_glossary(text="EW")
        assert "has no definition for" in json.dumps(robo_response)

        # the request was recorded in the interactions table
        interaction_check = db_session.query(Interaction).first()
        assert interaction_check is not None
        assert interaction_check.user_name == "testuser"
        assert interaction_check.term == "EW"
        assert interaction_check.action == "not_found"

    def test_get_definition_with_image(self, testcase, db_session, handle_glossary):
        ''' We can get a properly formatted definition with an image from the bot
        '''
        # set & test a definition
        handle_glossary(text="EW = http://example.com/ew.gif")

        filter = Definition.term == "EW"
        definition_check = db_session.query(Definition).filter(filter).first()
        assert definition_check is not None
        assert definition_check.term == "EW"
        assert definition_check.definition == "http://example.com/ew.gif"

        robo_response = handle_glossary(text="EW")
        testcase.assertDictEqual({
            'text': '*EW*: http://example.com/ew.gif',
            'blocks': [
                {'type': 'section', 'text': {'type': 'mrkdwn', 'text': '*EW*: http://example.com/ew.gif'}},
                {'type': 'image', 'image_url': 'http://example.com/ew.gif', 'alt_text': '*EW*: http://example.com/ew.gif'},
            ]
        }, robo_response)

    def test_set_alias(self, db_session, handle_glossary):
        ''' An alias can be set for a definition
        '''
        # set & test a definition and some aliases
        original_term = "Glossary Bot"
        first_alias = "Gloss Bot"
        second_alias = "Glossbot"
        third_alias = "GB"
        definition = "A Slack bot that maintains a glossary of terms created by its users, and responds to requests with definitions."
        handle_glossary(text="{original_term} = {definition}".format(**locals()))
        handle_glossary(text="{first_alias} = see {original_term}".format(**locals()))
        handle_glossary(text="{second_alias} = see also {original_term}".format(**locals()))
        handle_glossary(text="{third_alias} = See {original_term}".format(**locals()))

        # ask for the original definition
        robo_response = handle_glossary(text=original_term)
        assert robo_response is not None
        assert robo_response == f'*{original_term}*: {definition}'

        # ask for the second alias
        robo_response = handle_glossary(text=second_alias)
        assert robo_response is not None
        assert robo_response == f'*{original_term}*: {definition}'

        # ask for the third alias
        # (making sure we're case-insensitive)
        robo_response = handle_glossary(text=third_alias)
        assert robo_response is not None
        assert robo_response == f'*{original_term}*: {definition}'

    def test_delete_definition(self, db_session, handle_glossary):
        ''' A definition can be deleted from the database
        '''
        # first set a value in the database and verify that it's there
        handle_glossary(text="EW = Eligibility Worker")

        filter = Definition.term == "EW"
        definition_check = db_session.query(Definition).filter(filter).first()
        assert definition_check is not None
        assert definition_check.term == "EW"
        assert definition_check.definition == "Eligibility Worker"

        # now delete the value and verify that it's gone
        robo_response = handle_glossary(text="delete EW")
        assert "has deleted the definition for" in json.dumps(robo_response)

        definition_check = db_session.query(Definition).filter(filter).first()
        assert definition_check is None

    def test_get_stats(self, db_session, handle_glossary):
        ''' Stats are properly returned by the bot
        '''
        # set and get a definition to generate some stats
        handle_glossary(text="EW = Eligibility Worker")
        handle_glossary(text="EW")

        robo_response = handle_glossary(text="stats")
        assert "I have definitions for 1 term" in str(robo_response)
        assert "1 person has defined terms" in str(robo_response)
        assert "I've been asked for definitions 1 time" in str(robo_response)


    def test_get_stats_on_empty_database(self, db_session, handle_glossary):
        ''' A coherent message is returned when requesting stats on an empty database
        '''
        robo_response = handle_glossary(text="stats")

        assert "I don't have any definitions" in str(robo_response)
        assert "Nobody has defined terms" in str(robo_response)
        assert "Nobody has asked me for definitions" in str(robo_response)

    def test_get_learnings(self, db_session, handle_glossary):
        ''' Learnings are properly returned by the bot
        '''
        # set some values in the database
        letters = ["K", "L", "M", "N", "Ó", "P", "Q", "R", "S", "T", "U", "V"]
        for letter in letters:
            handle_glossary(text="{letter}W = {letter}ligibility Worker".format(letter=letter))

        robo_response = handle_glossary(text="learnings")

        assert "I recently learned definitions for" in robo_response
        assert "KW" in robo_response
        assert "LW" in robo_response
        assert "MW" in robo_response
        assert "NW" in robo_response
        assert "ÓW" in robo_response
        assert "PW" in robo_response
        assert "QW" in robo_response
        assert "RW" in robo_response
        assert "SW" in robo_response
        assert "TW" in robo_response
        assert "UW" in robo_response
        assert "VW" in robo_response

    def test_random_learnings(self, handle_glossary):
        ''' Learnings are returned in random order when requested
        '''
        # set some values in the database
        letters = ["E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S"]
        for letter in letters:
            handle_glossary(text="{letter}W = {letter}ligibility Worker".format(letter=letter))

        # get chronological learnings
        robo_response = handle_glossary(text="learnings")
        control = robo_response

        # get a few random learnings
        robo_response = handle_glossary(text="learnings random")
        random1 = robo_response

        robo_response = handle_glossary(text="learnings random")
        random2 = robo_response

        robo_response = handle_glossary(text="learnings random")
        random3 = robo_response

        # if they're all equal, we've failed
        assert control != random1
        assert control != random2
        assert control != random3

    def test_alphabetical_learnings(self, db_session, handle_glossary):
        ''' Learnings are returned in random order when requested
        '''
        # set some values in the database
        letters = ["E", "G", "I", "K", "M", "O", "Q", "S", "R", "P", "N", "L", "J", "H", "F"]
        check = []
        for letter in letters:
            handle_glossary(text="{letter}W = {letter}ligibility Worker".format(letter=letter))
            check.insert(0, "{}W".format(letter))

        desc_check = check[:12]
        alpha_check = list(check)
        alpha_check.sort()
        alpha_check = alpha_check[:12]

        # get chronological learnings
        robo_response = handle_glossary(text="learnings")
        assert ", ".join(map(lambda str: f"*{str}*", desc_check)) in robo_response

        # get alphabetical learnings
        robo_response = handle_glossary(text="learnings alpha")
        assert ", ".join(map(lambda str: f"*{str}*", alpha_check)) in robo_response

    def test_random_offset_learnings(self, db_session, handle_glossary):
        ''' An offset group of learnings are returned randomized
        '''
        # set some values in the database
        letters = ["E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S"]
        for letter in letters:
            handle_glossary(text="{letter}W = {letter}ligibility Worker".format(letter=letter))

        # get chronological learnings
        robo_response = handle_glossary(text="learnings 7 4")
        control = robo_response

        # get a list of the terms from the control string
        check_terms = control.split(', ')
        check_terms[0] = check_terms[0][-2:]

        # get a few random learnings
        robo_response = handle_glossary(text="learnings random 7 4")
        random1 = robo_response

        robo_response = handle_glossary(text="learnings random 7 4")
        random2 = robo_response

        robo_response = handle_glossary(text="learnings random 7 4")
        random3 = robo_response

        # if they're all equal, we've failed
        assert control != random1
        assert control != random2
        assert control != random3

        # but they should all have the same elements
        for term in check_terms:
            assert term in random1
            assert term in random2
            assert term in random3

    def test_all_learnings(self, db_session, handle_glossary):
        ''' All learnings are returned when requested
        '''
        # set some values in the database
        letters = ["E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X"]
        check = []
        for letter in letters:
            handle_glossary(text="{letter}W = {letter}ligibility Worker".format(letter=letter))
            check.insert(0, "{}W".format(letter))

        # get all learnings
        robo_response = handle_glossary(text="learnings all")
        assert ", ".join(map(lambda str: f"*{str}*", check)) in json.dumps(robo_response)

        # if 'all' is part of the command, other limiting params are ignored
        robo_response = handle_glossary(text="learnings all 5")
        assert ", ".join(map(lambda str: f"*{str}*", check)) in json.dumps(robo_response)

        robo_response = handle_glossary(text="learnings 5 3 all")
        assert ", ".join(map(lambda str: f"*{str}*", check)) in json.dumps(robo_response)

        robo_response = handle_glossary(text="learnings all 3 5")
        assert ", ".join(map(lambda str: f"*{str}*", check)) in json.dumps(robo_response)

    def test_some_learnings(self, db_session, handle_glossary):
        ''' Only a few learnings are returned when requested
        '''
        # set some values in the database
        letters = ["E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X"]
        for letter in letters:
            handle_glossary(text="{letter}W = {letter}ligibility Worker".format(letter=letter))

        limit = 7
        check = ["{}W".format(item) for item in list(reversed(letters[-limit:]))]

        # get some learnings
        robo_response = handle_glossary(text="learnings {}".format(limit))
        assert ", ".join(map(lambda str: f"*{str}*", check)) in json.dumps(robo_response)

    def test_offset_learnings(self, db_session, handle_glossary):
        ''' An offset of learnings are returned when requested
        '''
        # set some values in the database
        letters = ["E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X"]
        for letter in letters:
            handle_glossary(text="{letter}W = {letter}ligibility Worker".format(letter=letter))

        limit = 7
        offset = 11
        check = ["{}W".format(item) for item in list(reversed(letters[-(limit + offset):-offset]))]

        # get some learnings
        robo_response = handle_glossary(text="learnings {} {}".format(limit, offset))
        assert ", ".join(map(lambda str: f"*{str}*", check)) in json.dumps(robo_response)

    def test_learnings_language(self, db_session, handle_glossary):
        ''' Language describing learnings is numerically accurate
        '''
        # ask for recent definitions before any have been set
        robo_response = handle_glossary(text="learnings")
        assert "I haven't learned any definitions yet." in json.dumps(robo_response)

        # when one value has been set
        handle_glossary(text="EW = Eligibility Worker")
        robo_response = handle_glossary(text="learnings")
        assert "I recently learned the definition for" in json.dumps(robo_response)

        # when more than one value has been set
        handle_glossary(text="FW = Fligibility Worker")
        robo_response = handle_glossary(text="learnings")
        assert "I recently learned definitions for" in json.dumps(robo_response)

    def test_learnings_alternate_command(self, db_session, handle_glossary):
        ''' Learnings are returned when sending the 'recent' command.
        '''
        # ask for recent definitions before any have been set
        robo_response = handle_glossary(text="recent")
        assert "I haven't learned any definitions yet." in json.dumps(robo_response)

        # when one value has been set
        handle_glossary(text="EW = Eligibility Worker")
        robo_response = handle_glossary(text="recent")
        assert "I recently learned the definition for" in json.dumps(robo_response)

        # when more than one value has been set
        handle_glossary(text="FW = Fligibility Worker")
        robo_response = handle_glossary(text="recent")
        assert "I recently learned definitions for" in json.dumps(robo_response)

    def test_learnings_alternate_command_echoed(self, handle_glossary):
        ''' The learnings alternate command is echoed in the bot's reponse
        '''
        alternate_action = "recent"

        robo_response = handle_glossary(text=alternate_action)
        assert robo_response == "I haven't learned any definitions yet."

    def test_get_help(self, db_session, handle_glossary):
        ''' Help is properly returned by the bot
        '''
        # testing different chunks of help text with each response
        robo_response = handle_glossary(text="help")
        assert "to show the definition for a term" in json.dumps(robo_response)

        robo_response = handle_glossary(text="?")
        assert "to set the definition for a term" in json.dumps(robo_response)

        robo_response = handle_glossary(text="")
        assert "to delete the definition for a term" in json.dumps(robo_response)

        robo_response = handle_glossary(text=" ")
        assert "to see this message" in json.dumps(robo_response)

    def test_bad_set_commands(self, db_session, handle_glossary):
        ''' We get the right error back when sending bad set commands
        '''
        robo_response = handle_glossary(text="EW =")
        assert "You can set definitions like this" in json.dumps(robo_response)

        robo_response = handle_glossary(text="=")
        assert "You can set definitions like this" in json.dumps(robo_response)

        robo_response = handle_glossary(text="= = =")
        assert "You can set definitions like this" in json.dumps(robo_response)

    def test_bad_image_urls_rejected(self, handle_glossary):
        ''' Bad image URLs are not sent in the attachment's image_url parameter
        '''
        self.maxDiff = None

        # set some definitions with bad image URLs
        handle_glossary(text="EW = http://kittens.gif")
        handle_glossary(text="FW = httpdoggie.jpeg")
        handle_glossary(text="GW = http://stupid/goldfish.bmp")
        handle_glossary(text="HW = http://s.mlkshk-cdn.com/r/13ILU")

        robo_response = handle_glossary(text="EW")
        assert '*EW*: http://kittens.gif' == robo_response

        robo_response = handle_glossary(text="FW")
        assert '*FW*: httpdoggie.jpeg' == robo_response

        robo_response = handle_glossary(text="GW")
        assert '*GW*: http://stupid/goldfish.bmp' == robo_response

        robo_response = handle_glossary(text="HW")
        assert '*HW*: http://s.mlkshk-cdn.com/r/13ILU' == robo_response

if __name__ == '__main__':
    import pytest
    pytest.main()

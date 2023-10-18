Changelog for glossary-bot
===========================

## 2.0.1 (unreleased)
---------------------

- no functional changes, just configuring zest releaser


## 2.0.0 (2023-10-17)
------------------

- Major refactor to support mysql as well as postgres
- fuzzy matching in memory instead of postgres specific logic
- switch to python-bolt for slack communication, which lets us run in websocket mode (no public incoming access needed)
- /glossary is for you only, @glossary-bot is for public

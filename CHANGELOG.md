Changelog for glossary-bot
===========================

## Unreleased
[Compare the full difference.](https://github.com/halkeye/\glossary-bot/compare/2.0.1...HEAD)

- no functional changes, just configuring bump-my-version


## 2.0.0 (2023-10-17)

- Initial my version
- Major refactor to support mysql as well as postgres
- fuzzy matching in memory instead of postgres specific logic
- switch to python-bolt for slack communication, which lets us run in websocket mode (no public incoming access needed)
- /glossary is for you only, @glossary-bot is for public

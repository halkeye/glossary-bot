# Glossary Bot

Glossary Bot is a Slack bot that maintains a glossary of terms created by its users, and responds to requests with definitions.

It is a simple web app designed to be used as a [Slack app](https://api.slack.com/apps/).

![DemoGif](https://raw.githubusercontent.com/halkeye/glossary-bot/master/static/gloss-bot-demo.gif)

## Configuration

All Configuration is done by env variables

 * DATABASE_URL - Database url. Only postgresql:// and mysql:// are tested
 * SLACK_APP_TOKEN - [Slack app](https://api.slack.com/apps/) token.
    * Click **Generate Token and Scopes**. Make sure `connections:write` and `authorizations:read` scopes are set. Copy this into `SLACK_APP_TOKEN` variable in Digital Ocean
 * SLACK_BOT_TOKEN - [Slack app](https://api.slack.com/apps/) bot token.
    * Click **OAuth && Permissions**. Copy the `Bot User OAuth Token` and paste the token into `SLACK_BOT_TOKEN` variable in Digital Ocean
 * SLACK_SIGNING_SECRET - [Slack app](https://api.slack.com/apps/) signing token.
    * Should be on the main screen as signing secret
 * SLASH_COMMAND - Listen to a different slash command. By default this is /glossary

## Deploy Glossary Bot

Glossary Bot is a [Slack Bolt](https://slack.dev/bolt-python/concepts/) app built to run on any hosting provider. Private or public. Digital Ocean Apps Platform instructions have been provided below. To install the bot locally for development and testing, read [INSTALL](INSTALL.md).

### Set Up on Slack

Glossary Bot uses the new socket support, so it is very easy to setup.

First [create a new app](https://api.slack.com/apps?new_app=1) by copying the [manifest.json](./manifest.json) into the manifest text box.

### Deploy on Digital Ocean

[![Deploy to DO](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/halkeye/glossary-bot/tree/master)

Click the button above to get started. In the form that loads, add a name for your bot in the **App Name** field, or leave it blank to have Digitalocean generate a unique name. You won't see this name in Slack, it'll just be part of the URL that Slack uses to communicate with the bot behind the scenes.

And now you're good to get glossing! Open up Slack and type `/glossary help` to start.

## Releasing

```
npm install
npx semantic-release
```

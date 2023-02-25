# Notion-To-iCal

A little service I made for getting my Notion tasks (databse entries)
as a subscribable iCal feed.

## Features

* 🧙‍♂️🪄 Automagically creates .ical-files from events in a Notion database.
* 🌐 With example web server for hosting the generated files
* 🔧 Customizable database format
* ℹ️ Supports the following Notion database fields:
  * `title`
  * `text`
  * `date`
  * `multi_select` (only first entry)
* 🔋 Batteries included (Dockerfiles)

## Installation

### Prerequisites

* [Retrieve a Notion API key](https://www.notion.so/my-integrations).
* Share the database you want the script to access with your Notion integration.
* Know the IDs of your Notion database entries (try 
`curl --request POST \
  --url https://api.notion.com/v1/databases/<YOUR-DATABASE-UUID>/query \
  --header 'Authorization: Bearer <YOUR-AUTHENTICATION-TOKEN>' \
  --header 'Notion-Version: 2022-06-28'` to find out)

### Configuration

Before you can run the check, you have to configure at least a few things.
Rename `example-config.toml` to `config.toml`.
Open up the `config.toml` file and start editing!
There are comments in the file, so editing should be quite straightforward.

### Running the scripts

#### Pure commands

If you just want the bare commands required for running the project, here they are:

##### For updating calendars

* `python calendar_updater.py` to update once
* `python periodically_run_calendar_updater.py` to continuously update

##### For servering calendars using a server

* `python server.py` if development server is configured
* `gunicorn server:create_app()` to run with a WSGI server

#### Using Docker

The project already provides a `docker-compose.yml` example as well as two dockerfiles:
* `Dockerfile.updater` - Dockerfile for periodically updating the iCal files.
* `Dockerfile.server` -  Dockerfile for running the server that hosts iCal files.

##### Using Okteto

I'm hosting this for free on a new provider I tried out called [Okteto](https://www.okteto.com/). It was really straightforward!
If you're new to it [follow the installation instructions for their CLI](https://www.okteto.com/docs/getting-started/).
It's not necessary, but if you want an `okteto.yml` file and set up a development environment,
then write `okteto init` in a terminal. 
Otherwise, simply write `okteto deploy --build` both when initially publishing your applicaiton and every time you want to update
it.

### Accessing the calendars

Unless you have changed the URL path in the configuration file, the calendar is available at
`<http|https>://<your-server-url>/calendars/calendar_name?key=<authentication-key>`

**This is the URL that you add to all your calendar apps/managers!**

if authentication is disabled (see the configuration file), you may omit the `?key` part.
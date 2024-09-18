# Project Description

Parsers for Telegram.

> [!NOTE]
> Project is under development!

# Project Structure

```
.
├── compose.yml
├── configs
│   ├── logging.py
│   ├── public-channels.json
│   └── tg-keys.json
├── dashboard
│   ├── app.py
│   ├── DashboardDockerfile
│   ├── pages
│   │   ├── table.py
│   │   └── trend.py
│   ├── requirements_dynamo.txt
│   ├── requirements.txt
│   └── utils
│       ├── dynamodb.py
│       ├── fetch_data.py
│       └── mongodb.py
├── env
│   ├── config.env
│   ├── mongo.env
│   └── mongo-express.env
├── README.md
├── requirements.txt
├── src
│   ├── channel_parser.py
│   ├── crawler.py
│   ├── form_chats_list.py
│   ├── live_parser.py
│   └── ParserDockerfile
└── utils
    ├── channel_helpers.py
    ├── message_helpers.py
    ├── repo
    │   ├── cli.py
    │   ├── dynamo.py
    │   ├── interface.py
    │   ├── local.py
    │   └── mongo.py
    └── tg_helpers.py

```


# Local Deployment

### Python environment

Configure Python envronment from `requirements.txt` in a preferred way.

(Fully dockerized version coming later.)

### Launch a database
1. Setup the environment by creating the following `.env` files (it's better to add them as secrets in swarm):

 - `./env/mongo.env`
```
MONGO_INITDB_ROOT_USERNAME=root
MONGO_INITDB_ROOT_PASSWORD=example
```

 - (optional) `./env/mongo-express.env`
```
ME_CONFIG_MONGODB_ADMINUSERNAME=root
ME_CONFIG_MONGODB_ADMINPASSWORD=example
ME_CONFIG_MONGODB_URL=mongodb://root:example@mongo:27017/
ME_CONFIG_BASICAUTH=false
```
2. Launch the mongoDB with `docker compose up -d mongo`.

(Optional) Or `docker compose up -d mongo mongo-express` if you also want mongo-express UI.

### Configure Parser

1. Create an `./env/config.env` file
```
MESSAGE_REPO=mongo (use "local" to save to json or "cli" to just print them to STDOUT)
MESSAGE_TABLE=messages
MESSAGE_COLLECTION=test_batch

CHANNEL_REPO=mongo ("local" to save to a json file)
CHANNEL_TABLE=channels
CHANNEL_COLLECTION=parsing_list
PARSE_SUBSRIPTIONS=yes
NON_SUBBED_CHANNELS_LIST=./configs/public-channels.json

DB_USER=root
DB_PASSWD=example
DB_IP=172.20.0.2
DB_PORT=27017

TG_KEYS_FILE=./configs/tg-keys.json
LOG_CONFIG=./configs/log_config.json
```
2. To run parsers locally (not in a container) run `export CONFIG_PATH=./env/config.env`.
3. Setup a telegram account and subscribe it to the channels and chats you want to parse.
4. Get your telegram API keys (for that specific account) from https://my.telegram.org/ and put them into `./configs/tg-keys.json` file (move them to secrets too)
```
{
    "api_id": <id>,
    "api_hash": "<hash>",
    "session_name": "parser",
}
```
5. Run `python src/form_chats_list.py` to auto generate a list of channels to parse:
- (optional) before running the script, create a chat with yourself. Then it will be much easier to test the script and database connection.
- if `PARSE_SUBSRIPTIONS=yes` it will add all the subscriptions (including private chats) to parsing list.
- if you want to parse some public channels without subscribing, add their names (the ones that are used in t.me/channel_name urls, not titles!) to `NON_SUBBED_CHANNELS_LIST`. This option is useless for live parser, since it gets triggered by events on your account (no subscription -> no event in case of a new post)
```
[
    "channelname"
]
```
- During this first connection attempt you'll be asked to enter a confirmation code.
- Authentication will be saved in the `<session_name>.session` file (SQLite database) and as long as it persists you shouldn't be prompted to enter the code again (at least I hope so).
- You can also login with bot token (`tg_client.start(bot_token=)`), but iterating over dialogs don't work with it. I think you can still use bot token in the parser itself (step 6), but at this point there is no benefit.
- Maybe try disabling 2FA and login with you phone and password directly to avoid confirmation code on first login `tg_client.start(phone=, password=)`.
6. If you don't want to parse all of you subscriptions, just delete corresponding chats from the list.

### Using Parsers

Launch live parser `python src/live_parser.py` or `docker compose run -e PARSER=[live/channel] parser`. It will use already existing session file to login without confirmation code.

Alternatively, parse channel history with `python src/channel_parser.py`. It has multiple ways to specify number of posts to parse in `iter_messages()`:
- `limit=n` to parse last $n$ posts from each channel
- by post id ranges: `max_id` and `min_id`
- from specific `offset_date` up until now (note that you can't *directly* specify a range between two arbitrary dates)
- filter posts by some criteria

### Dashboard

(Optional) Launch a dashboard by running `docker compose up -d dashboard` and then go to http://localhost:8050/.

(Check that env variables in dockerfile are correct)
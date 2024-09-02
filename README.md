# Project Description

Live parser for channels and chats to which you're subscribed to on Telegram.

# Project Structure

```
.
├── compose.yml
├── dashboard
│   ├── app.py
│   └── pages
│       ├── table.py
│       └── trend.py
├── env
│   ├── config.env
│   ├── mongo.env
│   └── mongo-express.env
├── README.md
├── requirements.txt
├── src
│   ├── form_chats_list.py
│   └── parser.py
├── tg-keys.json
└── utils
    ├── chats_to_parse.json
    ├── db_helpers.py
    └── parser_helpers.py
```


# Running the Project

### Python environment

Configure Python envronment from `requirements.txt` in a preferred way.

(Fully dockerized version coming later.)

### Launch a database
1. Setup the environment by creating the following `.env` files:

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

(Optional) Or `docker compose up -d` if you also want mongo-express UI.

### Configure Parser

1. Create an `./env/config.env` file
```
DB_USER=root
DB_PASSWD=example
DB_IP=<mongo-container-ip>
DB_PORT=27017
TABLE_NAME=messages
COLLECTION_NAME=test_sample2

TG_KEYS_FILE=./tg-keys.json
CHANNEL_LIST_FILE=./utils/chats_to_parse.json
```
2. Setup a telegram account and subscribe it to the channels and chats you want to parse.
2. Get your telegram API keys (for that specific account) from https://my.telegram.org/ and put them into `./tg-keys.json` file
```
{
    "api_id": <id>,
    "api_hash": "<hash>",
    "session_name": "parser",
}
```
4. Run `python src/form_chats_list.py` to auto generate a list with IDs of *all* the channels and chats that you are subscribed to. During this first connection attempt you'll be asked to enter a confirmation code. It will be saved in the `<session_name>.session` file and as long as that file persists you shouldn't be prompted to enter the code again (at least I hope so).
5. If you don't want to parse all of you subscriptions, just delete corresponding chats from `./utils/chats_to_parse.json`.
6. Launch the parser `python src/parser.py`

### Dashboard

Launch a dashboard by running `python dashboard/app.py`.

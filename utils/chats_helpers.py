import json

from telethon.tl.types import InputChannel, PeerChannel, PeerUser, PeerChat


def get_dialog_list(client, chats):

    chat_names = chats.keys()
    chat_ids = chats.items()

    chats = []
    for dialog in client.iter_dialogs():
        if (dialog.name in chat_names
                or dialog.entity.id in chat_ids):

            chats.append(InputChannel(
                dialog.entity.id,
                dialog.entity.access_hash))
    print(len(chats))
    return chats


with open('./utils/chats_to_parse.json', 'r', encoding='utf-16') as f:
    chats = json.load(f)

names_dict = {val: key for key, val in chats.items()}


def get_chat_name(id):
    return names_dict[id]


def get_event_id(event):
    peer_id = event.message.peer_id
    if isinstance(peer_id, PeerChannel):
        return event.message.peer_id.channel_id
    elif isinstance(peer_id, PeerUser):
        return event.message.peer_id.user_id
    elif isinstance(peer_id, PeerChat):
        return event.message.peer_id.chat_id
    else:
        raise Exception('Anonymous message?')

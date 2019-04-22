import asyncio
import subprocess

from sophie_bot import bot, MONGO, OWNER_ID
from sophie_bot.modules.main import term, chat_term
from sophie_bot.events import register
from sophie_bot.modules.notes import button_parser


@register(incoming=True, pattern="^/term")
async def event(event):
    message = event.text
    if event.from_id not in OWNER_ID:
        msg = await event.reply("Running...")
        await asyncio.sleep(2)
        await msg.edit("Blyat can't do it becuase u dumb.")
        return
    msg = await event.reply("Running...")
    command = str(message)
    command = str(command[6:])
    
    result = "**Shell:**\n"
    result += await chat_term(event, command)

    await msg.edit(result)


@register(incoming=True, pattern="^/broadcast ?(.*)")
async def event(event):
    if event.from_id not in OWNER_ID:
        return
    chats = MONGO.chat_list.find({})
    raw_text = event.message.text.split(" ", 1)[1]
    text, buttons = button_parser(event.chat_id, raw_text)
    if len(buttons) == 0:
        buttons = None
    msg = await event.reply("Broadcasting to {} chats...".format(chats.count()))
    num_succ = 0
    num_fail = 0
    for chat in chats:
        try:
            await bot.send_message(chat['chat_id'], text, buttons=buttons)
            num_succ = num_succ + 1
        except Exception as err:
            num_fail = num_fail + 1
            await msg.edit("Error:\n`{}`.\nBroadcasting will continues.".format(err))
            await asyncio.sleep(2)
            await msg.edit("Broadcasting to {} chats...".format(chats.count()))
    await msg.edit(
        "**Broadcast completed!** Message sended to `{}` chats successfully, `{}` didn't received message.".format(
            num_succ, num_fail
        )) 
    


@register(incoming=True, pattern="^/sbroadcast ?(.*)")
async def event(event):
    if event.from_id not in OWNER_ID:
        return
    text = event.message.text.split(" ", 1)[1]
    # Add chats to sbroadcast list
    chats = MONGO.chat_list.find({})
    MONGO.sbroadcast_list.drop()
    MONGO.sbroadcast_settings.drop()
    for chat in chats:
        MONGO.sbroadcast_list.insert_one({'chat_id': chat['chat_id']})
    MONGO.sbroadcast_settings.insert_one({
        'text': text,
        'all_chats': chats.count(),
        'recived_chats': 0
    })
    await event.reply("Smart broadcast planned for `{}` chats".format(chats.count()))

# Check on smart broadcast 
@register(incoming=True)
async def event(event):
    chat_id = event.chat_id
    match = MONGO.sbroadcast_list.find_one({'chat_id': chat_id})
    if match:
        try:
            raw_text = MONGO.sbroadcast_settings.find_one({})['text']
            text, buttons = button_parser(event.chat_id, raw_text)
            if len(buttons) == 0:
                buttons = None
            await bot.send_message(chat_id, text, buttons=buttons)
        except Exception as err:
            print(err)
        MONGO.sbroadcast_list.delete_one({'chat_id': chat_id})
        old = MONGO.sbroadcast_settings.find_one({})
        num = old['recived_chats'] + 1
        MONGO.sbroadcast_settings.update(
            {'_id':old['_id']}, {
                'text': old['text'],
                'all_chats': old['all_chats'],
                'recived_chats': num
            }, upsert=False)
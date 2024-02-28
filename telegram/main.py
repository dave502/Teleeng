import asyncio
import json
from pyrogram import Client, filters, compose, idle
from pyrogram.types import (Message, ReplyKeyboardMarkup, InlineKeyboardMarkup,
                            InlineKeyboardButton,
                            InlineQueryResultArticle, InputTextMessageContent)
from pyrogram.raw.functions.channels import CreateForumTopic, GetForumTopicsByID
from pyrogram.raw import functions
from pyrogram.raw.types import ForumTopicDeleted
from pyrogram.handlers import MessageHandler
from pyrogram.enums import ChatType
from datetime import datetime
from dotenv import dotenv_values
from os import getenv
import logging
from  sys import stdout
import re
from urllib.parse import urlparse, parse_qs, quote
from pyrogram.errors.exceptions.bad_request_400 import PeerIdInvalid, ChannelInvalid, UsernameInvalid, UsernameNotOccupied

local_vars = dotenv_values(".env")

API_ID = getenv("APP_api_id") or local_vars["APP_api_id"]
API_HASH = getenv("APP_api_hash") or local_vars["APP_api_hash"]
BOT_TOKEN = getenv("BOT_TOKEN") or local_vars["BOT_TOKEN"]

CHAT = -1002015941224
FILTER_TOPIC = 1882

# asyncio.run(compose([app,bot], sequential=True))
async def main():

    # Временно оставляю бота, но, вероятнее всего, его можно будет убрать
    app = Client("user_bot",  api_id=API_ID, api_hash=API_HASH)
    bot = Client("bot_bot",  api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    # list of tracking sources
    filter = []
    # list of messages with filters (for delete event)
    filter_messages = set()
    # dynamic handlers
    chats_filter_handler = None
    private_filter_handler = None

    logging.basicConfig(level=logging.INFO, stream=stdout)

    apps = [app, bot]

    # #####################################################
    # #
    # # Parse service url in message
    # #
    # #####################################################
    # async def get_service_url(text: str) -> str|None:
    #     if text:
    #         try:
    #             #service_url = r"^\|\shttps:\/\/t\.me\/\S+?(?=\s\|)"
    #             service_url = r"https:\/\/t\.me\/\S+"
    #             matches = re.finditer(service_url, text, re.IGNORECASE)
    #             for match in matches:
    #                 return text[match.start():match.end()]
    #         except Exception as err:
    #             logging.error(f"Error while parsing text {text}", err)
    #     return None


    # async def parse_message(message: Message, dir="l"):
    #     service_url = await get_service_url(message.text)

    #     try:
    #         parsed_url = urlparse(service_url)
    #         msg_path = parsed_url.path.split('/')
    #     except TypeError as err:
    #         logging.error(f"Failed to parse url {service_url}", err)

    #     if dir == "l":
    #         clean_answer = message.text.lstrip(service_url).strip()
    #     else:
    #         clean_answer = message.text.rstrip(service_url).strip()

    #     # text, chat id, message id, query
    #     return clean_answer, int(msg_path[-2]), int(msg_path[-1]), parsed_url.query


    async def parse_url(url: str) -> tuple[str|int]:
        try:
            parsed_url = urlparse(url)
            msg_path = parsed_url.path.split('/')
        except TypeError as err:
            logging.error(f"Failed to parse url {url}", err)

        group = int(msg_path[-2]) if msg_path[-2].lstrip('-').isnumeric() else "@"+msg_path[-2]
        msg = int(msg_path[-1])

        return group, msg, parsed_url.query


    #####################################################
    #
    # Handle filter settings
    #
    #####################################################

    # filter messages from FILTER topic
    async def is_in_filter_topic(_, __, query):
        """

        """
        return query.reply_to_message_id == FILTER_TOPIC

    in_filter_topic = filters.create(is_in_filter_topic)

    # filter deleted messages from set of fliter messages
    async def is_in_filter_ids(_, __, query):
        return query.id in filter_messages

    in_filter_ids = filters.create(is_in_filter_ids)

    # update handlers with list of filter conditions
    @app.on_deleted_messages(in_filter_ids)
    @app.on_edited_message(in_filter_topic)
    @app.on_message(in_filter_topic)
    @app.on_message(filters.command("save"))
    async def update_filter(client, message):
        nonlocal chats_filter_handler, filter

        # clear all handlers
        filter.clear()
        filter_messages.clear()

        if chats_filter_handler:
            app.remove_handler(*chats_filter_handler)
        if private_filter_handler:
            app.remove_handler(*private_filter_handler)

        # add new handlers
        await init_filter(client)

        chats_filter_handler = app.add_handler(MessageHandler(question_handler, filters.chat(filter)&~filters.me))

        # if it was command "/save" delete it
        if isinstance(message, Message) and \
            message.text and message.text.startswith("/"):
            await message.delete()


    # read messages from FILTER topic and update the list of filter conditions
    async def init_filter(client):
        nonlocal private_filter_handler, filter, filter_messages

        async for msg in app.get_discussion_replies(CHAT, FILTER_TOPIC):
            if msg.text and not msg.text.startswith("/"):
                # if was word "private" - make handler for incoming messages
                if msg.text == "private":
                    private_filter_handler = app.add_handler(
                        MessageHandler(question_handler,
                                    (filters.private & ~filters.outgoing) &
                                    ~filters.bot))
                    continue
                elif msg.text.lstrip('-').isnumeric():
                    name = int(msg.text)
                elif msg.text.startswith('@'):
                    name = msg.text
                else:
                    url = urlparse(msg.text)
                    name = url.path.replace("/", '@', 1)
                filter.append(name)
                filter_messages.add(msg.id)
                try:
                    chat_obj = await app.get_chat(name)
                    if chat_obj.linked_chat:
                        filter.append(chat_obj.linked_chat.id)
                except Exception:
                    pass


    #####################################################
    #
    # Handle messages according to filter
    #
    #####################################################

    async def question_handler(client, message):
        """
        handle all private messages and messages in groups
        """
        if (not message.from_user) or message.service:
            return

        #
        # get or create user's topic in the forum
        #

        # get topic title (username + user's id)
        topic_title = (message.from_user.first_name or message.from_user.username) + ' ' + str(message.from_user.id)

        # find user's topic
        channel = await client.resolve_peer(CHAT)

        forum = await client.invoke(
                functions.channels.GetForumTopics(
                    channel=channel, offset_date=-1, offset_id=-1, offset_topic=-1, limit=999)
            )
        topic = [topic for topic in forum.topics if (not isinstance(topic, ForumTopicDeleted)) and topic.title==topic_title]

        if topic:
            topic = topic[0]
        else:
            # if not such topic - create one
            topics  = await client.invoke(
                functions.channels.CreateForumTopic(
                    channel=channel,
                    title = topic_title,
                    random_id=message.from_user.id,
                    icon_color=0x6FB9F0,
                )
            )

            # may be some lag after topic creating so wait a little for a new topic
            retries = 0
            while not topic:
                await asyncio.sleep(2)

                forum = await client.invoke(
                        functions.channels.GetForumTopics(
                            channel=channel, offset_date=-1, offset_id=-1, offset_topic=-1, limit=999)
                    )
                topic = topic = [topic for topic in forum.topics if (not isinstance(topic, ForumTopicDeleted)) and topic.title==topic_title]
                topic = topic[0] if topic else None

                retries += 1
                if retries == 10:
                    logging.fatal("can't find the user's topic")

            """
            Send topic's pin message with information about user ->
            """
            # user's name and surname
            user =  "\nuser: " + (message.from_user.first_name or "") + " " + (message.from_user.last_name or "")

            # username with link to user
            if message.from_user.username:
                username = f"\nusername: [{message.from_user.username}](https://t.me/{message.from_user.username})"
            else:
                username = ""

            # user_id with link to user
            user_id = f"\nuser_id: [{message.from_user.id}](tg://user?id={message.from_user.id})"

            # all info together
            user_info = user + username + user_id

            # send first message to topic with user's info
            msg_user_info = await app.send_message(
                chat_id=CHAT,
                text=user_info,
                disable_web_page_preview=True,
                reply_to_message_id=topic.id,
            )

            await msg_user_info.pin()
            """
            <-
            """

        #
        # compose info about user message
        #

        # if message is personal - create link to dialog
        if message.chat.type == ChatType.PRIVATE:
            source = f"[personal](tg://openmessage?user_id={message.from_user.id})"
            message_link = ""
        # if message is from channel or group - create link to chat or group
        elif message.chat.type == ChatType.CHANNEL or message.chat.type == ChatType.SUPERGROUP:
            # if message is comment - get name of the chat
            if message.reply_to_message and \
                message.reply_to_message.forward_from_chat and \
                message.reply_to_message.forward_from_chat.title: \
                title = message.reply_to_message.forward_from_chat.title
            else:
                title = message.chat.title

            if message.reply_to_message and \
                message.reply_to_message.forward_from_chat and \
                message.reply_to_message.forward_from_chat.username: \
                source = f"`{title}` [link](t.me/{message.reply_to_message.forward_from_chat.username})"
            else:
                source = f"`{title}` [link]({message.link[:message.link.rfind('/')]})"

            message_link = f"[Сообщение]({message.link})"
        else:
            source = f"`{message.chat.title}`"


        #original_msg_info = f"[⠀](msg.info/{message.chat.id}/{message.id})"
        message_info = f"{source} {message_link} \n"
        if message.text:
            message_info += f"[Ответ GPT](https://someapi.com/?text={quote(message.text)}&chat={message.chat.id}&msg={message.id})"


        #
        # forward user's message to topic
        #
        msg_frwrd_updates = await client.invoke(
            functions.messages.ForwardMessages(
                from_peer= await client.resolve_peer(message.chat.id),
                id=[message.id],
                random_id=[client.rnd_id()],
                to_peer=await client.resolve_peer(CHAT),
                top_msg_id=topic.id
            )#
        )

        #
        # send message with user's message info
        #
        msg_frwrd = await app.get_messages(CHAT, msg_frwrd_updates.updates[0].id)
        res = await msg_frwrd.reply(message_info,
                                     quote=False,
                                     disable_web_page_preview=True,
                                     reply_to_message_id=topic.id)

        # msg_answer = await app.send_message(
        #     chat_id=CHAT,
        #     text=message_info,
        #     disable_web_page_preview=True,
        #     reply_to_message_id=msg_frwrd.updates[0].id,#topic.id,
        # )

        # #
        # # send bot's message with proposal to generate an answer
        # #
        # buttons= [[
        #     InlineKeyboardButton('🤖 GPT Answer', callback_data='generate_answer'),
        # ]]
        # reply_markup = InlineKeyboardMarkup(buttons)

        # msg_answer = await bot.send_message(
        #     chat_id=CHAT,
        #     text=message_info,
        #     disable_web_page_preview=True,
        #     reply_to_message_id=msg_frwrd.updates[0].id,#topic.id,
        #     reply_markup=reply_markup
        # )

        #print(msg_answer)


    #####################################################
    #
    # Handle callback to generate GPT answer
    #
    #####################################################
    @bot.on_callback_query(filters.regex(f'^generate_answer'), group=CHAT)
    async def generate_answer(client, callback_query):

        try:
            msg_url = re.findall("message_link: (.+(?=\n|$))", callback_query.message.text)[0]
            chat_id, message_id, _ = await parse_url(msg_url)
        except Exception as err:
            logging.error(f"Failed to parse message info {callback_query.message.text} ", err)

        try:

            ...
            answer = "GPT Answer"
            ...

            # answer_msg = await callback_query.message.reply_to_message.reply_text(
            #     "answer",
            #     quote=False,
            #     disable_web_page_preview=True,
            #     reply_to_message_id=callback_query.message.reply_to_message.reply_to_message_id
            # )

            buttons= [[
                InlineKeyboardButton('✏️  Edit', switch_inline_query_current_chat=f"id:{callback_query.message.id}\n{answer}"),
                #InlineKeyboardButton('🗃️  Save', callback_data='save_answer'),
                InlineKeyboardButton('📨  Send', callback_data=f'send_answer->{chat_id}:{message_id}')
            ]]
            reply_markup = InlineKeyboardMarkup(buttons)
            await callback_query.message.edit_text(callback_query.message.text + "\n" +
                                                   f"answer:\n{answer}",
                                                   disable_web_page_preview=True)
            await callback_query.message.edit_reply_markup(reply_markup)
            await callback_query.answer("Answer is ready", show_alert=False)

        except PeerIdInvalid as err:
            logging.error(f"Failed to send message to chat_id {chat_id}", err)


    #####################################################
    #
    # Handle callback to send answer to the user
    #
    #####################################################
    @bot.on_callback_query(filters.regex(f'^send_answer'), group=CHAT)
    async def send_answer(client, callback_query):
        chat_id, msg_id = callback_query.data.split("->")[1].split(":")
        text = callback_query.message.text[
            callback_query.message.text.find("answer:\n") + len("answer:\n"):
            ]

        msg_answer = await app.send_message(
            chat_id=int(chat_id) if chat_id.lstrip('-').isnumeric() else chat_id,
            text=text,
            disable_web_page_preview=True,
            reply_to_message_id=int(msg_id),
        )

        # new_buttons = [[button for button in callback_query.message.reply_markup.inline_keyboard[0] \
        #             if button.callback_data and not button.callback_data.startswith("send_answer")]]
        # await callback_query.message.edit_reply_markup(InlineKeyboardMarkup(new_buttons))
        try:
            ...
            #await callback_query.message.edit_reply_markup(None)
        except Exception as err:
            logging.warning(err)

        await callback_query.answer("Answer was sent", show_alert=False)


    #####################################################
    #
    # Handle callback to save answer to the database
    #
    #####################################################
    @bot.on_callback_query(filters.regex(f'save_answer'), group=CHAT)
    async def save_answer(client, callback_query):
        ...
        await callback_query.answer("Answer was saved", show_alert=False)


    #####################################################
    #
    # Show Links for edited answer to Save and to Send
    #
    #####################################################
    @bot.on_inline_query(group=CHAT)
    async def inline_menu(client, inline_query):


        if not inline_query.query:
            return

        # try:
        #     start = inline_query.query.index("%")+1
        #     if not start: return
        #     end = inline_query.query.index("%", start)
        #     url = inline_query.query[start:end]
        # except Exception as err:
        #     return

        # question_url = await get_service_url(inline_query.query)
        # if not question_url:
        #     return

        if inline_query.query[:3] != ("id:"):
            logging.warning("inline query doesn't have message's id")
            return

        sep = inline_query.query.find("\n")
        # bot_msg_id = inline_query.query[3:sep]
        # text = inline_query.query[sep:]

        results = []
        results.append(InlineQueryResultArticle(
                id="1",  # ссылки у нас уникальные, потому проблем не будет
                title="Save and send",
                description="Save answer to database and send to user",
                # url=url+"/savesend/",
                # hide_url=True,
                input_message_content=InputTextMessageContent(
                        message_text= inline_query.query[:sep] + ":savesend\n" + \
                        # "&action=savesend" + "\n" +
                        inline_query.query[sep:].strip(),
                    disable_web_page_preview=True
                )
            ))
        results.append(InlineQueryResultArticle(
                id="2",  # ссылки у нас уникальные, потому проблем не будет
                title="Just send",
                description="Just send answer to user without saving the answer",
                # url=url+"/send/",
                # hide_url=True,
                input_message_content=InputTextMessageContent(
                        message_text= inline_query.query[:sep] + ":send\n" + \
                        # "&action=savesend" + "\n" +
                        inline_query.query[sep:].strip(),
                    disable_web_page_preview=True
                )
            ))

        results.append(InlineQueryResultArticle(
                id="3",  # ссылки у нас уникальные, потому проблем не будет
                title="Just edit",
                description="Just edit the answer",
                input_message_content=InputTextMessageContent(
                        message_text= inline_query.query[:sep] + ":edit\n" + \
                        inline_query.query[sep:].strip(),
                    disable_web_page_preview=True
                )
            ))

        await inline_query.answer(results, is_personal=True)


    #####################################################
    #
    # Receive and process the inline via_bot request
    # with new answer with action parameters
    #
    #####################################################
    @bot.on_message(filters.chat(CHAT) & filters.via_bot)
    async def new_answer_handler(client, message):
        """
        handle messages with new answers
        """
        # answer, chat_id, msg_id, msg_query = await parse_message(message , "l")

        if message.text[:3] != ("id:"):
            logging.warning("viabot message doesn't have message's id")
            return

        sep = message.text.find("\n")
        bot_msg_id, action = message.text[3:sep].split(":")
        bot_msg_id = int(bot_msg_id)
        result = await message.delete()

        # query = parse_qs(msg_query)
        # answer_msg_id = int(query['a'][0])
        # action = query['action'][0]

        bot_msg = await client.get_messages(CHAT, bot_msg_id)

        new_reply = bot_msg.reply_markup
        new_reply.inline_keyboard[0][0].switch_inline_query_current_chat = \
            f"id:{bot_msg_id}\n{message.text[sep:].strip()}"

        try:
            bot_msg = await client.edit_message_text(
                chat_id=CHAT, #message.chat.id,
                message_id=bot_msg_id,
                text=bot_msg.text[:bot_msg.text.find("answer:\n")+len("answer:\n")] +
                    message.text[sep:].strip(),
                reply_markup=new_reply
            )
        except Exception as err:
            logging.error(err)


        if action == "savesend" or action == "send":

            send_btn = [button for button in bot_msg.reply_markup.inline_keyboard[0] \
                            if  button.callback_data and button.callback_data.startswith("send_answer")]
            await app.request_callback_answer(CHAT, bot_msg_id, send_btn[0].callback_data)

            if action == "savesend":
            #     await client.request_callback_answer(CHAT, bot_msg_id, 'save_answer')

                ...

    #####################################################
    #
    # Receive and process the inline via_bot request
    # with new answer with action parameters
    #
    #####################################################
    # @bot.on_message(filters.chat(CHAT) & filters.reply)
    # async def new_answer_handler(client, message):


    for _app in apps:
        await _app.start()

    await update_filter(app, None)

    await idle()

    for _app in apps:
        await _app.stop()


asyncio.run(main())
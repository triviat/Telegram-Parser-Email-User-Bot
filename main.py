from telethon import TelegramClient
from telethon import functions, types, errors
from telethon.tl.types import InputChannel
from openpyxl import Workbook

from time import sleep
import os.path

from config import *

try:
    wb = Workbook()
    file = 'data.xlsx'

    users_data = wb.active
    users_data.title = "users"

    wb.save(filename=file)
except Exception as exc:
    print(exc)

client = TelegramClient('user', api_id, api_hash)
limit = 100000


async def save_user(username: str or None, phone: str or None) -> bool:
    if (username is None) and (phone is None):
        return False

    users_data.append([username, phone])

    return True


async def get_users(chat) -> None:
    counter = 0
    saved_users = 0
    offset = 0

    chat_id = chat.entity.id
    chat_hash = chat.entity.to_dict().get('access_hash', 0)
    chat_object = InputChannel(chat_id, chat_hash)

    print(f'{chat.title}: ', end='')

    while True:
        try:
            participants = await client(functions.channels.GetParticipantsRequest(
                                    channel=chat_object,
                                    filter=types.ChannelParticipantsSearch(''),
                                    offset=offset,
                                    limit=limit,
                                    hash=chat_hash
                                    ))
            users = participants.users
            if not users:
                break

            for user in users:
                if await save_user(user.username, user.phone):
                    saved_users += 1

            users_count = len(users)

            offset += users_count
            counter += users_count

            sleep(0.1)
        except errors.rpcerrorlist.ChannelInvalidError:
            print('Ошибка получения хеша.', end=' ')
            break

    print(f'Сохранено {saved_users} пользователей')
    wb.save('data.xlsx')


async def get_chats_and_channels():
    chats = await client.get_dialogs()
    with open('channels.txt', encoding='UTF-8') as f:
        input_channels = [line.strip() for line in f.readlines()]

    print('\nНачинаю...\n')

    for chat in chats:
        if chat.is_group and (chat.name in input_channels):
            input_channels.remove(chat.name)
            await get_users(chat)

    print('\nЗакончил!\n')


async def start_sending_messages():
    file_name = await get_file_name()
    message = await get_message()
    user_delay = await get_user_delay()
    time_delay = await get_time_delay()

    with open(file_name) as f_users:
        users = [user.strip() for user in f_users.readlines()]

    print('\nОтправляю...')
    counter = 0
    for user in users:
        if await send_message(user, message):
            counter += 1
            if (user_delay > 0) and (counter % user_delay == 0):
                print(f'Отправил сообщение {user_delay} пользователям и встал на паузу в {time_delay} секунд...')
                sleep(time_delay)

    print('Закончил.')
    print(f'Сообщение было отправлено {counter} пользователям из {len(users)}\n')


async def send_message(user: str, message: str) -> bool:
    try:
        await client.send_message(entity=user, message=message)
        return True
    except Exception as exception:
        print(exception)
        return False


async def get_file_name():
    file_name = input('Укажите полное название файла (например: users.txt): ')
    while True:
        if os.path.exists(file_name):
            return file_name
        else:
            print(f'Не вижу {file_name}\nФайл должен быть в папке: {os.getcwd()}')
            file_name = input('Попробуйте еще раз: ')


async def get_message():
    message = input('Отлично. Теперь укажите сообщения, которое хотите разослать пользователям: ')
    while True:
        if message.strip() != '':
            return message
        else:
            message = input('Нельзя отправить пустое сообщение. Введите пожалуйста другое: ')


async def get_time_delay():
    try:
        delay = float(input('Укажите время задержки: '))
        return delay
    except ValueError:
        return -1


async def get_user_delay():
    try:
        delay = int(input('Укажите через какое количество аккаунтов выполнять задержку: '))
        return delay
    except ValueError:
        return -1


async def main():
    while True:
        choice = str(input('Выберите действие:\n1. Спарсить чаты\n2. Сделать рассылку\n0. Закончить работу\n')).strip()
        if choice == '1':
            await get_chats_and_channels()
        elif choice == '2':
            await start_sending_messages()
        elif choice == '0':
            print('До свидания.')
            return
        else:
            print('Ошибка. Введите цифру, которая вам нужна, и нажмите Enter.')


if __name__ == '__main__':
    try:
        print('Здравствуйте.')
        with client:
            client.start()
            client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        print('До свидания.')

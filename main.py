import telebot
import requests
import json
import os
import time
import datetime

from threading import Thread
from bs4 import BeautifulSoup


class TelBot:
    def __init__(self, BOT_TOKEN, get_bot_link):
        self.BOT_TOKEN = BOT_TOKEN
        self.get_bot_link = get_bot_link
        base_file_path = os.path.dirname(os.path.abspath(__file__))
        self.filename = f'{base_file_path}/users.json'
        self.users = read_from_json()
        self.bot = telebot.TeleBot(BOT_TOKEN)


    def start_bot(self):
    
        @self.bot.message_handler(commands=['start'])
        def welcome(message):
            status = False
            telegram_userid = f"{message.chat.id}"
            telegram_username = message.chat.username if message.chat.username else message.chat.first_name
            self_users = read_from_json()
            self.users = read_from_json()
            
            if 'verify' in message.text:
                verify_code = message.text.split('verify=')[-1].strip()
                get_userid, is_status = self.save_pickle(message, verify_code)
                if get_userid:
                    if not self.check_access(message):
                        status = True
                        text = f'Welcome `{telegram_username}`, \n\nYou are Now Connected to the Bot! \nWhen Result is Out, You Get Notification!'
                    else:
                        text = f"Hi `{telegram_username}`, \n\nYou Are Already Connected to the Bot! \nWhen Result is Out, You Get Notification! \nGet More Info: /info"
                    
                    self.update_user(self.users, telegram_userid, telegram_username, get_userid, verify_code)
                elif is_status == 'true':
                    text = f"Hi `{telegram_username}` \n\nWe are Unable to Verify Your Token! \nBut You Get Notification When Result is Out!"
                    status = True
                else:
                    text = f"Invalid Token, \n\nClick Here To Get Token!👇 \n {self.get_bot_link}?notify={telegram_userid}"
                    if self.check_access(message):
                        text = f"Hi `{telegram_username}` \n\nToken Is Invalid!, 👇 \nBut You are Already Connected to the Bot!"
            else:
                if self.check_access(message):
                    text = f"hi `{telegram_username}`, \nWhen Result is Out, You Get Notification!\nGet More Info: /info"
                else:
                    text = f"You are Not Connected to the bot! \n\nClick Here to Connect!👇 \n{self.get_bot_link}?notify={telegram_userid}"
                    self.update_user(self.users, telegram_userid, telegram_username, '', '')
            
            f_text = ''
            s_text = ''
            t_text = ''
            if status == False:
                status_ = self.check_access(message, self_users, True)
            else:
                status_ = self.check_access(message)
            
            if status_ == None:
                f_text = f"Hello `{telegram_username}`,"
            elif status_ == False:
                if telegram_username:
                    f_text = f"Hello `{telegram_username}`, \nglad you're here with GtuNotificationBot!"
                else:
                    f_text = "Hello, \nglad you're here with GtuNotificationBot!"
                
                s_text = f"When you're connected, \nYou'll Receive Notifications Like This: 👇\n\nResult Is Out: \n👉 `Result of BE SEM 4 - Regular (MAY 2024) Exam`"
                t_text = 'Get More Info: /info'
            
            if f_text:
                send_reply(self, message, [f_text, text, s_text, t_text])
            else:
                send_reply(self, message, [text])
            
            if status:
                texts = [
                    f"You'll Receive Notifications Like This: 👇\n\nResult Is Out: \n👉 `Result of BE SEM 4 - Regular (MAY 2024) Exam`",
                    "/current to see current result. \n\n/info to get more info."
                ]
                send_reply(self, message, texts)
                
            global first_notification
            
            if not first_notification:
                first_notification = True
                save_current_result()
                
                texts = [
                    'Your First Notification, Result Is Out: \n',
                    result_text,
                ]
                send_reply(self, message, texts)
    
        @self.bot.message_handler(commands=['info', 'help', 'about'])
        def get_info(message):            
            text = get_info_text()
            
            send_reply(self, message, [text])
    
        @self.bot.message_handler(commands=['auth', 'profile', 'name', 'profiles', 'setting', 'settings'])
        def authenticate_your(message):
            self.users = read_from_json()
            
            telegram_username = self.users[f'{message.chat.id}']['username']
            text = [
                "Your Details: 👇 \n", 
                f'Username: {telegram_username}'.title()
            ]
            
            send_reply(self, message, text)
    
        @self.bot.message_handler(commands=['current'])
        def get_current_result(message):
            current_result_thread = Thread(target=save_current_result, args=('Hello', self, message, ))
            current_result_thread.start()
    
        @self.bot.message_handler(commands=['notify'])
        def manage_notification(message):
            telegram_userid = f"{message.chat.id}"
            
            if self.check_access(message):
                text = [
                    "Currently, you are notified only when the GTU BE Branch results are out. \nTo view the current result: /current",
                    "We are working on additional notification features, \nsuch as sending all result notifications! \nStay Tuned!"
                ]
            
            else:
                text = [f"You are Not Connected to the bot! \nBut You Get Notification When Result is Out! \n\nClick Here to Connect! 👇 \n{self.get_bot_link}?notify={telegram_userid}"]
            
            send_reply(self, message, text)
    
        @self.bot.message_handler(commands=['users', 'user'])
        def get_users(message):
            self.users = read_from_json()
            
            text = []
            for i, j in self.users.items():
                text.append(f"User ID: {i} \nUsername: {j['username']} ")
            
            send_reply(self, message, [text])
    
        @self.bot.message_handler(commands=['sendmsg'])
        def sendmsg(message):        
            text = "Invalid Command Format! \n\nUse `/sendmsg userid=<userid> text=`<massage>"
            if 'text' in message.text:
                send_text = message.text.split('text=')[-1].strip()
                if send_text:
                    if 'userid=' in message.text:
                        text_userid = message.text.split('text=')[0].split('userid=')[-1].strip()
                        if send_text:
                            send_reply(self, message, [send_text], text_userid)
                            s_msg = f'{text_userid}'
                        else:
                            s_msg = False
                    else:
                        s_msg = False
                
                if not s_msg == False:
                    text = f"msg: `{send_text}`. \n\n Send To {s_msg}."
            
            send_reply(self, message, [text])
    
        @self.bot.message_handler(commands=['note', 'notes', 'assignment', 'assignments', 'resource', 'resources'])
        def get_resources(message):            
            text = """
*Resources:  📚* 
- Sem 3 Notes: https://cse-aiml.live/gtu/notes/sem3/
- Sem 4 Notes: https://cse-aiml.live/gtu/notes/sem4/
- Sem 5 Notes: https://cse-aiml.live/gtu/notes/sem5/
- Sem 6 Notes: https://cse-aiml.live/gtu/notes/sem6/

- Sem 6 Assignments: https://cse-aiml.live/gtu/assignments/sem6/
            """
            
            send_reply(self, message, [text])
    
        @self.bot.message_handler(commands=['contact', 'contactus', 'query', 'developer', 'developed', 'developerdby', 'email', 'mail', 'website', 'site'])
        def any_query(message):            
            text = """
*Contact Us: 💬*
- Email: info@cse-aiml.live
- Website: https://cse-aiml.live/gtu/contact-us/
- Developer: https://cse-aiml.live/gtu/developer/
            """
            
            send_reply(self, message, [text])
    
        @self.bot.message_handler(commands=['source_code', 'sourcecode', 'code', 'source', 'codes', 'demo', 'Repository'])
        def source_code(message):            
            text = """
**Source Code: 📁**
- Code Repository: 👇
https://cse-aiml.live/GtuNotificationBot/code/
            """
            
            send_reply(self, message, [text])
    
        @self.bot.message_handler(commands=['command', 'commands'])
        def command(message):
            text = """**Commands:** 🤖 
 - `/start verify=`<auth-token>: Connect With Bot
 ' `/info` : Get Information.'
 - `/auth`:  Authenticate your identity.
 - `/current`:  See current Result.
 - `/notify`:  Manage notification.
 - `/users` : Get All User.
 ' `/sendmsg userid=<userid> text=`<massage> : Send Message To Specific User',
 - `/note`:  Get Resources.
 - `/contact`:  Any Query.
 - `/code`: Get Source Code Of Bot."""
            
            send_reply(self, message, [text])
    
        @self.bot.message_handler(func=lambda msg: True)
        def send_reply_to_all_message(message):
            telegram_userid = f"{message.chat.id}"
            telegram_username = message.chat.username if message.chat.username else message.chat.first_name
            self.users = read_from_json()
            
            if message.text == "info" or message.text == "help" or message.text == "about":
                text = get_info_text()
            else:
                if self.check_access(message):
                    text = f"hi `{telegram_username}`, \nWhen Result is Out, You Get Notification! \nGet More Info: /info"
                else:
                    text = f"You are Not Connected to the bot! \n\nClick Here to Connect! 👇 \n{self.get_bot_link}?notify={telegram_userid}"
                    
            send_reply(self, message, [text])

        self.bot.infinity_polling()

    # Check User is Connected or Not
    def check_access(self, message, self_users=None, check=False):
        if self_users == None:
            self_users = self.users
        telegram_userid = f"{message.chat.id}"
        if telegram_userid in self_users:
            if self_users[telegram_userid]['userid']:
                return True
            if check:
                return None
        
        return False

    # Save and Update Data From JSON
    def update_user(self, users, user_id, username, userid, token, msg='yes'):
        """Update or add a user to the dictionary and save to a JSON file."""
        users[user_id] = {'username': username, 'userid': userid, 'token': token, 'msg': msg}
        save_to_json(users)
        
        self.users = read_from_json()

    # Save Message To Server 2
    def save_pickle(self, message, tokens='', site_userid=None):
        return 1, 'yes'


# Info Command
# Get Information Text
def get_info_text():
    return """
**GtuNotificationBot** ℹ️  
 - sends alerts when GTU BE Branch results 
   are declared and notifies users about 
   updates from cse-aiml.live. 
 
 - It features user authentication, 
   customization collaboration, and ensures 
   timely notifications, enhancing user 
   engagement and information delivery.

**Commands:** 🤖
 - `/start verify=`<auth-token>: Connect With Bot
 ' `/info` : Get Information.'
 - `/auth`:  Authenticate your identity.
 - `/current`:  See current Result.
 - `/notify`:  Manage notification.
 - `/users` : Get All User.
 ' `/sendmsg userid=<userid> text=`<massage> : Send Message To Specific User',
 - `/note`:  Get Resources.
 - `/contact`:  Any Query.
 - `/code`: Get Source Code Of Bot.

**Features:** 🌟
 -**Result Notifications:** 
   sends alerts when GTU BE Branch results 
   are declared
 -**Update Alerts:** 
   Posts updates from cse-aiml.live.
 -**User Authentication:** 
   Ensures secure interaction.
 -**Customization Support:** 
   Collaborates on customizations and user 
   preferences.
    """


# Send Reply To User Using Bot Object
def send_reply(self, message, text, chat_id=None, parse_mode='Markdown'):
    parse_mode = '' if parse_mode == False else parse_mode
    if not chat_id:
        chat_id = f'{message.chat.id}'
    for i in text:
        try:
            self.bot.send_message(chat_id=chat_id, text=f"{i}", parse_mode=parse_mode)
        except:
            pass


# Send Reply To User Using Request
def request_get(text, chat_id):
    # Construct the API URL
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    # The Text
    text = "Result Is Out: \n" + "\n".join(text)

    # Parameters for the API request
    params = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    # Send the HTTP request
    try:
        requests.get(url, params=params)
    except Exception as e:
        print(f"Error For Request Get: {e}")
        try:
            requests.get(url, params=params)
        except Exception as e:
            print(f"Error Again For Request Get: {e}")


# Get All Registered User From Server
def get_all_user():
    users = read_from_json()
    user_list = [i for i, j in users.items()]
    
    return user_list


# First Text Of Result Is Out List
def get_text(check=None, index=0):
    try:
        response = requests.get('https://www.gtu.ac.in/result.aspx', cookies=cookies, headers=headers)
        bs = BeautifulSoup(response.text, 'html.parser')
        text = bs.find_all('h3', class_='Content')[index].find_all('a')[0].text
    except Exception as e:
        print(f'Error: {e}')
        text = ''
    
    if text:
        return text
    
    if check:
        return text
    
    if not text:
        for i in range(3):
            text = get_text(True)
            if text:
                break
            else:
                time.sleep(1)
                text = 'Result of IC SEM 2 - Regular (MAY 2024) Exam'
    
    return text


"""
    -----------------------------------  Read and Update Data From JSON Start ----------------------------------- 
"""

def read_from_json():
    """Read dictionary from a JSON file."""
    try:
        base_file_path = os.path.dirname(os.path.abspath(__file__))
        filename = f'{base_file_path}/users.json'
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_to_json(user_json):
    base_file_path = os.path.dirname(os.path.abspath(__file__))
    filename = f'{base_file_path}/users.json'
    with open(filename, 'w') as file:
        json.dump(user_json, file, indent=4)

"""
    -----------------------------------  Read and Update Data From JSON End -------------------------------------- 
"""


"""
    ------------------------ Check Result is Out or Not And Send Message To All User Start  ------------------------
"""

def get_sleep_time():
    adjusted_time = datetime.datetime.now().time()
    
    # Define the offset
    offset = datetime.timedelta(hours=5, minutes=30)
    
    # Adjust the current time with the offset
    adjusted_datetime = datetime.datetime.combine(datetime.date.today(), adjusted_time) + offset
    current_time = adjusted_datetime.time()
    
    # Define 9 AM time
    ten_am = datetime.time(9, 0, 0)

    # Check if current time is between 9 PM and 9 AM
    if datetime.time(21, 0, 0) <= current_time or current_time < ten_am:
        # Calculate time difference between 9 AM and current time
        if current_time < ten_am:
            time_difference = datetime.datetime.combine(adjusted_datetime.today(), ten_am) - datetime.datetime.combine(adjusted_datetime.today(), current_time)
        else:
            next_day_ten_am = datetime.datetime.combine(adjusted_datetime.today() + datetime.timedelta(days=1), ten_am)
            time_difference = next_day_ten_am - datetime.datetime.combine(adjusted_datetime.today(), current_time)

        sleep_time = time_difference.total_seconds()

        return True, sleep_time
    
    return False, 0


def main_run_function(text):
    time_wait = 10
    count_min = 0
    count_for = 0
    while True:
        print('Start =>', text)
        while True:
            check, status = check_result_is_out(text)
            time_status, sleep_time = get_sleep_time()
            if status == False and check:
                text = check
            if status:
                text = check
                time_wait = 5
                count_min += 1
                break
            else:
                if time_status:
                    print(f'Script Ended, Sleeping for {sleep_time} seconds until 9 AM...')
                    time.sleep(sleep_time)
                else:
                    if time_wait == 5:
                        if count_for == 48:
                            count_min = 0
                            count_for = 0
                            time_wait = 10
                        if count_min == 2:
                            count_min = 0
                            count_for = 0
                            time_wait = 10
                        count_for += 1
                    minutes = time_wait * 60
                    print(f'Script Ended, Sleeping for {time_wait} Minutes...')
                    time.sleep(minutes)
                print('Woke up from sleep And \nStart =>', text)


def check_result_is_out(text_1s):
    response = requests.get('https://www.gtu.ac.in/result.aspx', cookies=cookies, headers=headers)
    bs = BeautifulSoup(response.text, 'html.parser')
    text = bs.find_all('h3', class_='Content')[0].find_all('a')[0].text
    if text != f'{text_1s}':
        main_result_list = []
        for i in range(10):
            temp_text = bs.find_all('h3', class_='Content')[i].find_all('a')[0].text
            
            if temp_text == text_1s:
                break
            main_result_list.append(f'👉 `{temp_text}`')
        
        current_result_thread = Thread(target=save_current_result, args=(bs, ))
        current_result_thread.start()
        
        if main_result_list:
            send_msg(main_result_list)
            print(main_result_list)
            print('Getting Result and Send Message')
            check_token_is_valid(True)
            return text, True
        else:
            check_token_is_valid(True)
            return text, False
    
    else:
        check_token_is_valid(True)
        return False, False


def save_current_result(soup=None, self=None, message=None):
    try:
        global result_text
        try:
            main_list = []            
            element = soup.find(class_='result-list-outer').find('li')
            count = 0
            for i in element.find_all(['a', 'span']):
                count += 1
                if count == 1:
                    text = f'Declared Date: {i.text}'
                elif count == 2:
                    text = f'👉 `{i.text}`'
                elif count == 3:
                    text = f'Re-check/Assess Application Deadline: {i.text.split(":")[-1]}'
                else:
                    break
                
                main_list.append(text)
            
            f = "\n".join(main_list)
        except:
            f = result_text
        
        result_text = f
        if self:
            text = [
                result_text,
                'Full List Here 👇\nhttps://cse-aiml.live/gtu-result/'
            ]
            
            send_reply(self, message, text, chat_id=None)
            
            self.send_text_to_me(message, result_text)
    
    except Exception as e:
        print(f"Error For Save Current Result: {e}")


def send_msg(send_text):
    try:        
        send_message_list = get_all_user()
        if send_message_list:
            global first_notification
            if not first_notification:
                first_notification = True
        for i in send_message_list:
            request_get(send_text, i)
            print('Message Sent')
    except:
        pass

"""
    ------------------------  Check Result is Out or Not And Send Message To All User End   ------------------------
"""


def bot_start_message(info):
    return f"""

Performing system checks...

Your Bot is Started! 🤖
Bot Info: 👇
    - Bot ID: {info['id']}
    - Bot Name: {info['first_name']}
    - Bot Username: {info['username']}

Starting the bot server at :
    - https://web.telegram.org/k/#@{info['username']}
    - https://t.me/{info['username']}/ 


The bot is now running and ready to accept commands! 🚀
Type /start to get started!

"""


def bot_error_message():
    text = "               " + '^' * len(BOT_TOKEN)
    return f"""
Performing system checks...


*Error: 🚫*
    - BOT_TOKEN = "{BOT_TOKEN}" 
    {text}
    
    TokenError: Invalid Token! 
    
    - Your Bot Token Is Invalid! 
    - Please Check Your Bot Token And Try Again!
    - Check README.md File For More Info!

"""


def check_token_is_valid(check=None):
    bot = telebot.TeleBot(BOT_TOKEN)
    try:
        bot_info = bot.get_me()
        if check:
            global console_print
            
            if not console_print:
                print(bot_start_message(bot_info.to_dict()))
                console_print = True
        return True
    except:
        return False


if __name__ == '__main__':
    print('Script will starting soon...')
    """
                # Enter Your Bot Token Here
                # Document: Check README.md File
                # How To Get Bot Token: https://t.me/botfather
    """
    
    BOT_TOKEN = "YOUR_BOT_TOKEN"
    
    
    cookies = {
        'ASP.NET_SessionId': '1sn50nhfgdke3r0mqqldwxux',
        'AWSALBTG': 'WihM7i62yyrVRpxEmsaMjTbd1UvO5XIiYOwT1gZz7zLo/ZVNczo/KMIoL6ZxOjQ3XaXnWssWppp4V9Gc/z5wC4P69JdT+KwH/SBQyRsJnBPwqy4crBp90PcWDAjoPYTMc6uv6RlLw6pMcUBqZ2E/82Fl6W5O++NJqej9N9xwWPME',
        'AWSALBTGCORS': 'WihM7i62yyrVRpxEmsaMjTbd1UvO5XIiYOwT1gZz7zLo/ZVNczo/KMIoL6ZxOjQ3XaXnWssWppp4V9Gc/z5wC4P69JdT+KwH/SBQyRsJnBPwqy4crBp90PcWDAjoPYTMc6uv6RlLw6pMcUBqZ2E/82Fl6W5O++NJqej9N9xwWPME'
    }

    headers = {
        'authority': 'www.gtu.ac.in', 'accept-language': 'en-US,en;q=0.9', 'cache-control': 'max-age=0', 'upgrade-insecure-requests': '1',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'referer': 'https://www.google.com/', 'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"', 'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"', 'sec-fetch-dest': 'document', 'sec-fetch-mode': 'navigate', 'sec-fetch-site': 'cross-site', 'sec-fetch-user': '?1', 
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    }
    
    first_notification = False
    console_print = False
    
    result_text = get_text(index=1)
    
    # This is not required. This token is for testing purposes for @GTUNotificationBot.
    get_bot_link = "https://cse-aiml.live/gtu/notification/"
    
    if not check_token_is_valid():
        print(bot_error_message())
        exit(0)

    # This is for getting the result and sending the message to all users.
    run_thread = Thread(target=main_run_function, args=(result_text, ))
    run_thread.start()
    
    # This is for starting the bot.
    TelBot(BOT_TOKEN, get_bot_link).start_bot()

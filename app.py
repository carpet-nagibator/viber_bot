import json
import random
import sqlite3
from datetime import datetime
from Settings import TOKEN, WEBHOOK
from flask import Flask, request, Response
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.viber_requests import ViberMessageRequest, ViberConversationStartedRequest
from viberbot.api.messages import (
    TextMessage
)


class MyDataBase:
    def __init__(self, database_name):
        self.conn = sqlite3.connect(database_name, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        with open('create_schema.sql', 'rt') as f:
            query = f.read()
            cursor.executescript(query)
        self.conn.commit()
        cursor.close()

    def close(self):
        self.conn.close()

    def add_user(self, viber_id):
        query = """
        insert into users (viber_id)
        values (?)
        """
        try:
            self.conn.execute(query, (viber_id, ))
            self.conn.commit()
        except:
            self.conn.rollback()

    def send_question(self, viber_id):
        select_query = """
        select all_answers, correct_answers, user_id, dt_last_answer
        from users
        where viber_id = ?
        """
        ret_value = self.conn.execute(select_query, (viber_id,)).fetchone()
        if ret_value['all_answers'] >= 10:
            temp_correct_answers = ret_value['correct_answers']
            update_query = """
            update users set all_answers = 0, correct_answers = 0
            where viber_id = ?
            """
            self.conn.execute(update_query, (viber_id,))
            self.conn.commit()
            select_query2 = """
            select count(word)
            from learning
            where user_id = ? and right_answer > 4
            """
            ret_value2 = self.conn.execute(select_query2, (ret_value['user_id'],)).fetchone()
            return TextMessage(text=f'У вас {temp_correct_answers} верных из 10. '
                                    f'Вы уже выучили {ret_value2["count(word)"]} слов. '
                                    f'Осталось выучить {50 - ret_value2["count(word)"]} слов. '
                                    f'Последний опрос пройден {str(ret_value["dt_last_answer"])[:16]}. '
                                    f'Хотите ещё раз сыграть?',
                               keyboard=KEYBOARD1, tracking_data='tracking_data')
        else:
            temp_answers = []
            temp_correct_answer = 100
            question = {}
            while temp_correct_answer >= 5:
                question = random.choice(data)
                insert_query = """
                insert into learning (user_id, word)
                values (?, ?)
                """
                try:
                    self.conn.execute(insert_query, (ret_value['user_id'], question['word']))
                    self.conn.commit()
                except:
                    self.conn.rollback()
                select_query2 = """
                                select right_answer from learning
                                where user_id = ? and word = ?
                                """
                ret_value2 = self.conn.execute(select_query2, (ret_value['user_id'], question['word'])).fetchone()
                temp_correct_answer = ret_value2['right_answer']

            update_query = """
                        update users set question = ?
                        where viber_id = ?
                        """
            self.conn.execute(update_query, (str(question), viber_id))
            self.conn.commit()
            temp_answers.append(question['translation'])
            for i in range(3):
                temp_answers.append(random.choice(data)['translation'])
            random.shuffle(temp_answers)
            for i in range(4):
                KEYBOARD2['Buttons'][i]['Text'] = f'{temp_answers[i]}'
                KEYBOARD2['Buttons'][i]['ActionBody'] = f'{temp_answers[i]}'
            return TextMessage(text=f'{ret_value["all_answers"] + 1}.Как переводится слово {question["word"]}',
                               keyboard=KEYBOARD2, tracking_data='tracking_data')

    def check_answer(self, viber_id, user_answer):
        check = 'Неверно'
        select_query = """
                select question, user_id
                from users
                where viber_id = ?
                """
        ret_value = self.conn.execute(select_query, (viber_id,)).fetchone()
        question = eval(ret_value['question'])
        update_query = """
                update users set all_answers = all_answers + 1, dt_last_answer = ?
                where viber_id = ?
                """
        self.conn.execute(update_query, (datetime.now(), viber_id))
        self.conn.commit()
        if user_answer == question['translation']:
            update_query1 = """
                            update users set correct_answers = correct_answers + 1
                            where viber_id = ?
                            """
            self.conn.execute(update_query1, (viber_id,))
            self.conn.commit()
            update_query2 = """
                            update learning set right_answer = right_answer + 1, dt_last_answer = ?
                            where word = ? and user_id = ?
                            """
            self.conn.execute(update_query2, (datetime.now(), question['word'], ret_value['user_id']))
            self.conn.commit()
            select_query = """
                            select right_answer from learning
                            where word = ? and user_id = ?
                            """
            ret_value2 = self.conn.execute(select_query, (question['word'], ret_value['user_id'])).fetchone()
            check = f'Верно. Количество правильных ответов: {ret_value2["right_answer"]}'
        return TextMessage(text=check, keyboard=KEYBOARD2, tracking_data='tracking_data')

    def send_example(self, viber_id):
        select_query = """
                        select question
                        from users
                        where viber_id = ?
                        """
        ret_value = self.conn.execute(select_query, (viber_id,)).fetchone()
        question = eval(ret_value['question'])
        return TextMessage(text=f'{random.choice(question["examples"])}',
                           keyboard=KEYBOARD2, tracking_data='tracking_data')


db = MyDataBase("mydb.db")

app = Flask(__name__)
count = 0

bot_configuration = BotConfiguration(
    name='olddrunkenwolf',
    avatar='http://viber.com/avatar.jpg',
    auth_token=TOKEN
)

viber = Api(bot_configuration)


@app.route('/')
def hello():
    global count
    count += 1
    return f'Hello world {count}'


with open("english_words.json", "r", encoding='utf-8') as f:
    data = json.load(f)

KEYBOARD1 = {
"Type": "keyboard",
"Buttons": [
        {
            "Columns": 6,
            "Rows": 1,
            "BgColor": "#e6f5ff",
            "ActionBody": "Давай начнём!",
            "Text": "Давай начнём!"
        }
    ]
}

KEYBOARD2 = {
"Type": "keyboard",
"Buttons": [
        {
            "Columns": 3,
            "Rows": 1,
            "BgColor": "#e6f5ff"
        },
        {
            "Columns": 3,
            "Rows": 1,
            "BgColor": "#e6f5ff"
        },
        {
            "Columns": 3,
            "Rows": 1,
            "BgColor": "#e6f5ff"
        },
        {
            "Columns": 3,
            "Rows": 1,
            "BgColor": "#e6f5ff"
        },
        {
            "Columns": 6,
            "Rows": 1,
            "BgColor": "#e6f5ff",
            "ActionBody": "Показать пример",
            "Text": "Показать пример"
        }
    ]
}


@app.route('/incoming', methods=['POST'])
def incoming():
    viber_request = viber.parse_request(request.get_data())
    print(viber_request)
    if isinstance(viber_request, ViberConversationStartedRequest):
        # идентификация/добавление нового пользователя
        new_current_id = viber_request.user.id
        db.add_user(new_current_id)
        viber.send_messages(viber_request.user.id, [
            TextMessage(text='Бот предназначен для заучивания английских слов, для начала нажмите кнопку снизу.',
                        keyboard=KEYBOARD1, tracking_data='tracking_data')
        ])
    if isinstance(viber_request, ViberMessageRequest):
        current_id = viber_request.sender.id
        message = viber_request.message
        if isinstance(message, TextMessage):
            text = message.text
            print(text)
            # чтение введёного текста
            if text == "Давай начнём!":
                bot_response = db.send_question(current_id)
                viber.send_messages(current_id, bot_response)
            elif text == "Показать пример":
                bot_response = db.send_example(current_id)
                viber.send_messages(current_id, bot_response)
            else:
                bot_response_1 = db.check_answer(current_id, text)
                bot_response_2 = db.send_question(current_id)
                viber.send_messages(current_id, [bot_response_1, bot_response_2])
    return Response(status=200)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=80)

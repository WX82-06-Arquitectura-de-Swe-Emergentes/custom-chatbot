from flask import Flask, request, jsonify
import pyrebase
from creds import firebase_config, bot_id
from datetime import datetime
import os
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.agents.agent_types import AgentType
from langchain.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain.llms.openai import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.sql_database import SQLDatabase
import urllib

from promp_templates import SQL_LIMIT_PROMPT, TABLES_LIMIT_PROMPT

app = Flask(__name__)
os.environ["OPENAI_API_KEY"] = "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"

params = urllib.parse.quote_plus \
    (r'Driver={ODBC Driver 17 for SQL Server};Server=tcp:lifetr4vel-db.database.windows.net,'
     r'1433;Database=emergentes;Uid=iot_admin@lifetr4vel-db;Pwd=NexusNova2023;Encrypt=yes;TrustServerCertificate=no'
     r';Connection Timeout=30;')
conn_str = 'mssql+pyodbc:///?odbc_connect={}'.format(params)

firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()

""" 
db_connection = SQLDatabase.from_uri(conn_str,
                                     include_tables=["trip",
                                                     "destination",
                                                     "season",
                                                     "user",
                                                     "category"
                                                     ],
                                     )


llm = OpenAI(temperature=0, verbose=True)
db_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True)
"""


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


@app.route('/message', methods=['POST'])
def generate_and_save_message():
    body = request.get_json()
    chat_id = body['chat_id']
    print(chat_id)
    messages = body['messages']
    print(messages)

    message = generate_answer_test(messages)
    save_message(chat_id, message)

    return jsonify({'status': 'success'})


def save_message(chat_id, message):
    new_message = {
        'name': bot_id,
        'message': message,
        'timestamp': int(datetime.now().timestamp() * 1000)
    }

    db.child('messages').child(chat_id).push(new_message)

    db.child('chats').child(chat_id).update({
        "lastMessage": new_message['message'],
        "timestamp": new_message['timestamp'],
    })


def generate_answer_test(messages):
    return "test 3"

def generate_answer(messages):

    str_prompt = ""

    str_prompt += SQL_LIMIT_PROMPT
    str_prompt += TABLES_LIMIT_PROMPT

    for message in messages:
        str_prompt += message

    openai_answer = db_chain.run(str_prompt)
    return openai_answer


if __name__ == '__main__':
    app.run()

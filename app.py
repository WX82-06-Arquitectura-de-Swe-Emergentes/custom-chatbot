from flask import Flask, request, jsonify
import pyrebase
from creds import firebase_config, bot_id
from datetime import datetime
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.agents.agent_types import AgentType
from langchain.llms.openai import OpenAI
from langchain.sql_database import SQLDatabase

from promp_templates import SQL_LIMIT_PROMPT, TABLES_LIMIT_PROMPT

app = Flask(__name__)

conn_str = 'mssql+pyodbc://iot_admin:NexusNova2023@lifetr4vel-db.database.windows.net:1433/emergentes?driver=ODBC+Driver+17+for+SQL+Server'

firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()


db_connection = SQLDatabase.from_uri(conn_str,
                                     include_tables=["trip",
                                                     "destination",
                                                     "season",
                                                     "user",
                                                     "category"
                                                     ],
                                     )



llm = OpenAI(temperature=0, verbose=True)
toolkit = SQLDatabaseToolkit(db=db_connection, llm=OpenAI(model_name="davinci-002", temperature=0))

agent_executor = create_sql_agent(
    llm=OpenAI(temperature=0),
    toolkit=toolkit,
    verbose=True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
)

#db_chain = SQLDatabaseChain.from_llm(llm, db_connection, verbose=True)



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

    message = generate_answer(messages)
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

    if len(messages) > 1:
        str_prompt += "HISTORY: "
        for message in messages[:-1]:
            str_prompt += message + ", "

        str_prompt += "CURRENT QUESTION: " + messages[-1] + ":"
    else:
        str_prompt += messages[0]

    print(str_prompt)

    openai_answer = agent_executor.run(str_prompt)
    print(openai_answer)

    return openai_answer


if __name__ == '__main__':
    app.run()

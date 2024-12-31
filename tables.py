from loader import app, database
import flask
import config
from time import time

raw = """
<table>
  <tr>
    <th>Язык программирования</th>
    <th>Применение</th>
  </tr>
  <tr>
    <td>Python</td>
    <td>Научные вычисления, веб-разработка, автоматизация, анализ данных, машинное обучение</td>
  </tr>
  <tr>
    <td>JavaScript</td>
    <td>Веб-разработка (клиентская и серверная), создание интерактивных веб-приложений</td>
  </tr>
  <tr>
    <td>Java</td>
    <td>Разработка мобильных приложений (Android), корпоративные приложения, веб-приложения</td>
  </tr>
</table>
"""

def create_table(user_id: int, content: str):
    data = {
        "user_id": user_id,
        "content": content,
        "date": time()
    }
    database.create('tables', data)

def trim_tables(user_id: int):
    while True:
        tables = database.read('tables', filters={"user_id": user_id})
        if len(tables) > config.TABLES_PER_USER:
            old = oldest_table(tables)
            database.delete('tables', old)
        else:
            return

def oldest_table(tables: list[dict]):
    return min(tables, key=lambda table: table["date"])

@app.route('/')
def render_table():
    args = flask.request.args.to_dict()
    table_id = args.get('table_id')
    if table_id is None:
        return flask.render_template('error.html')
    
    table = database.read('tables', filters={"id": table_id})
    if len(table) == 0:
        return flask.render_template('error.html')

    content = table[0]["content"]

    return flask.render_template('table.html', table=content)
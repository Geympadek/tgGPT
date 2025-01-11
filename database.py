import sqlite3
from flask import Flask, request, jsonify
import json
import requests

def filters_to_query(filters: dict, logic = "AND"):
    """
    Converts dictionary of `filters` into `sqlite` query
    """
    query_filters = ""

    if filters:
        filters_list = []

        for field, condition in filters.items():
            query = f'{field} = "{condition}"'
            filters_list.append(query)
        
        query_filters = "where " + f" {logic} ".join(filters_list)
    return query_filters

class Database:
    """
    Abstract db class
    """
    def __init__(self):
        pass

    def create(self, table: str, data: dict):
        """
        Appends `data` into the database at `table`
        """
        pass

    def update(self, table: str, data: dict, filters: dict = None, logic: str = "AND"):
        """
        Replace value in the `table` with `data`
        \n`filters` - if not null, replaces only where the specified value is equal to filter
        """
        pass

    def read(self, table: str, filters: dict = None, logic: str = "AND") -> list[dict]:
        """
        Returns data as a dictionary. If filters can't be satisfied, returns `None`
        \n`filters` - if not null, returns a single row, else returns the whole table
        """
        pass

    def delete(self, table: str, filters: dict, logic: str = "AND"):
        """
        Removes data in `table`
        \n`filters` - removes only those where the specified key is equal to filter
        """
        pass

    def setdefault(self, table:str, data:dict):
        """
        Creates a new entry in the database if one doesn't exist yet
        Returns True if new entry created
        """
        try:
            self.create(table, data)
            return True
        except:
            return False

    def create_read(self, table: str, data: dict):
        """
        Creates a new entry in the database and reads it
        """
        self.create(table, data)
        return self.read(table, filters=data)[-1]

class FileDatabase(Database):
    def __init__(self, path: str):
        """
        Loads the database from the `path`
        """
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.cursor = self.connection.cursor()
    
    def create(self, table: str, data: dict):
        fields = []
        values = []

        for key, value in data.items():
            fields.append(key)
            values.append(value)

        marks = ', '.join(['?'] * len(fields))

        fields = ', '.join(fields)
        values = tuple(values)

        self.cursor.execute(f"INSERT INTO {table}({fields}) VALUES({marks})", values)
        self.connection.commit()
    
    def update(self, table: str, data: dict, filters: dict = None, logic: str = "AND"):
        query_filters = filters_to_query(filters, logic)

        for key, value in data.items():
            self.cursor.execute(f"UPDATE {table} SET {key} = ? {query_filters}", (value,))
        
        self.connection.commit()

    def read(self, table: str, filters: dict = None, logic: str = "AND") -> list[dict]:
        query_filters = filters_to_query(filters, logic)

        self.cursor.execute(f"SELECT * FROM {table} {query_filters}")

        keys = [description[0] for description in self.cursor.description]

        values = self.cursor.fetchall()
        return [dict(zip(keys, row)) for row in values]

    def delete(self, table: str, filters: dict, logic: str = "AND"):
        query_filters = filters_to_query(filters, logic)

        self.cursor.execute(f"DELETE FROM {table} {query_filters}")
        self.connection.commit()

IP = "127.0.0.1"
PORT = 5000
DB_ROUTE = "/database/"

FULL_URL = f"http://{IP}:{PORT}{DB_ROUTE}"

class WebDatabase(Database):
    def create(self, table: str, data: dict):
        response = requests.post(
            url=FULL_URL,
            params={"table": table},
            json=data
        )
        response.raise_for_status()
    
    def read(self, table: str, filters: dict = None, logic: str = "AND") -> list[dict]:
        params = {
            "table": table,
        }
        
        if filters is not None:
            params["filters"] = json.dumps(filters)
        
        response = requests.get(
            url=FULL_URL,
            params=params,
        )
        return response.json()
    
    def update(self, table: str, data: dict, filters: dict = None, logic: str = "AND"):
        params = {
            "table": table,
        }
        
        if filters is not None:
            params["filters"] = json.dumps(filters)
        
        response = requests.put(
            url=FULL_URL,
            params=params,
            json=data
        )
        response.raise_for_status()
    
    def delete(self, table: str, filters: dict, logic: str = "AND"):
        params = {
            "table": table,
        }
        
        if filters is not None:
            params["filters"] = json.dumps(filters)
        
        response = requests.delete(
            url=FULL_URL,
            params=params
        )
        response.raise_for_status()

def main():
    app = Flask('database')
    database = FileDatabase('database.db')

    def success():
        return jsonify({"message": "Success!"}), 200
    
    @app.route(DB_ROUTE, methods=['GET'])
    def read():
        args = request.args.to_dict()
        table = args["table"]
        
        filters = args.get("filters")
        if filters is not None:
            filters: dict = json.loads(filters)

        return database.read(table=table, filters=filters)

    @app.route(DB_ROUTE, methods=['POST'])
    def create():
        args = request.args.to_dict()
        table = args["table"]
        
        data = request.get_json()

        database.create(table=table, data=data)
        return success()

    @app.route(DB_ROUTE, methods=['PUT'])
    def update():
        args = request.args.to_dict()
        table = args["table"]

        filters = args.get("filters")
        if filters is not None:
            filters: dict = json.loads(filters)
        
        data = request.get_json()

        database.update(table=table, filters=filters, data=data)
        return success()

    @app.route(DB_ROUTE, methods=["DELETE"])
    def delete():
        args = request.args.to_dict()
        table = args["table"]

        filters = args.get("filters")
        if filters is not None:
            filters: dict = json.loads(filters)
        
        database.delete(table=table, filters=filters)
        return success()
    
    app.run(host=IP, port=PORT)

if __name__ == "__main__":
    main()
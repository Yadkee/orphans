#! python3
from mysql.connector import connect
from json import load


def main():
    with open("secret/config.json") as f:
        CONFIG = load(f)
    DB_ARGS = CONFIG["DB_ARGS"]
    cnx = connect(**DB_ARGS)
    cur = cnx.cursor()

    cur.execute("""create database telemanager;""")
    cur.execute("""use telemanager;""")
    cur.execute("""create table birthday (
        user INT UNSIGNED,
        date SMALLINT UNSIGNED,
        text VARCHAR(32)
    );
    """)
    cur.execute("""create table reminder (
        user INT UNSIGNED,
        date TIMESTAMP,
        text VARCHAR(140)
    );
    """)
    cur.execute("""create table event (
        user INT UNSIGNED,
        date DATE,
        text VARCHAR(140)
    );
    """)
    cur.execute("""create table tag (
        user INT UNSIGNED,
        date DATE,
        text VARCHAR(140),
        value TINYINT
    );
    """)
    cur.close()
    cnx.close()

if __name__ == "__main__":
    main()

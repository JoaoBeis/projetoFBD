import configparser
import functools
from pathlib import Path
import pyodbc

@functools.cache
def conn_string() -> str:
    config_file = Path(__file__).parent.parent / "conf.ini"
    assert config_file.exists(), "Ficheiro conf.ini não encontrado"

    config = configparser.ConfigParser()
    config.read(config_file)

    server = config["database"]["server"]
    db_name = config["database"]["name"]
    username = config["database"]["username"]
    password = config["database"]["password"]

    return (
        f"DRIVER={{SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={db_name};"
        f"UID={username};"
        f"PWD={password};"
        f"TrustServerCertificate=yes;"
    )

def create_connection():
    return pyodbc.connect(conn_string())
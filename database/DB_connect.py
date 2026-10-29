import pathlib
import mysql.connector
from mysql.connector import errorcode, pooling


class DBConnect:
    _cnxpool = None

    def __init__(self):
        raise RuntimeError("Non istanziare: usa DBConnect.get_connection()")

    @classmethod
    def get_connection(cls, pool_name="comodato_pool", pool_size=5):
        if cls._cnxpool is None:
            try:
                cls._cnxpool = pooling.MySQLConnectionPool(
                    pool_name=pool_name,
                    pool_size=pool_size,
                    option_files=f"{pathlib.Path(__file__).resolve().parent}/connector.cnf",
                )
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                    print("Utente o password del database errati")
                elif err.errno == errorcode.ER_BAD_DB_ERROR:
                    print("Il database non esiste")
                else:
                    print(err)
                return None
        return cls._cnxpool.get_connection()

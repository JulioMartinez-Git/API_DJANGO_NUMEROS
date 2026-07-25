import os
import sys
from pathlib import Path

import MySQLdb
from dotenv import load_dotenv


def main():
    base_dir = Path(__file__).resolve().parent.parent
    env_path = base_dir / ".env"
    load_dotenv(env_path)

    config = {
        "db_name": os.getenv("DB_NAME", "").strip(),
        "db_user": os.getenv("DB_USER", "").strip(),
        "db_password": os.getenv("DB_PASSWORD", ""),
        "db_host": os.getenv("DB_HOST", "127.0.0.1").strip(),
        "db_port": os.getenv("DB_PORT", "3306").strip(),
    }

    missing = [key for key, value in config.items() if key != "db_password" and not value]
    if missing:
        print("MySQL no esta configurado. Faltan variables en .env:")
        for key in missing:
            print(f"- {key.upper()}")
        return 2

    if not config["db_password"]:
        print("Aviso: DB_PASSWORD esta vacio. Se intentara conectar sin imprimir contrasena.")

    try:
        connection = MySQLdb.connect(
            host=config["db_host"],
            user=config["db_user"],
            passwd=config["db_password"],
            db=config["db_name"],
            port=int(config["db_port"]),
            charset="utf8mb4",
        )
        connection.close()
    except Exception as exc:
        print("No se pudo conectar a MySQL.")
        print(f"Base: {config['db_name']}")
        print(f"Host: {config['db_host']}:{config['db_port']}")
        print(f"Usuario: {config['db_user'] or '(vacio)'}")
        print(f"Error: {exc}")
        return 1

    print("Conexion MySQL exitosa.")
    print(f"Base: {config['db_name']}")
    print(f"Host: {config['db_host']}:{config['db_port']}")
    print(f"Usuario: {config['db_user']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

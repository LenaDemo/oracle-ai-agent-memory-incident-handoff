"""Prepare only this demo's dedicated local container and database user."""
import argparse
import os
from pathlib import Path
import secrets
import subprocess

ROOT = Path(__file__).resolve().parent
CONTAINER = "oracle-incident-demo"
VOLUME = "oracle-incident-demo-data"
IMAGE = "container-registry.oracle.com/database/free@sha256:cf540c3fa190d7cffad08c491652ac07fc70314e510f6b87890449517d565e94"


def initialize_env():
    path = ROOT / ".env"
    if path.exists():
        print("Keeping existing .env (values hidden).")
        return
    text = (ROOT / ".env.example").read_text()
    text = text.replace("replace_with_a_strong_admin_password", "A1" + secrets.token_hex(20))
    text = text.replace("replace_with_a_strong_application_password", "A1" + secrets.token_hex(20))
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as output:
        output.write(text)
    print("Created private .env with generated passwords. Values hidden.")


def start():
    initialize_env()
    found = subprocess.run(["docker", "container", "inspect", CONTAINER], capture_output=True)
    if found.returncode == 0:
        subprocess.run(["docker", "start", CONTAINER], check=True)
        return
    subprocess.run(["docker", "volume", "create", VOLUME], check=True)
    subprocess.run([
        "docker", "run", "-d", "--name", CONTAINER,
        "--label", "project=oracle-incident-handoff",
        "-p", "127.0.0.1:1522:1521", "--env-file", str(ROOT / ".env"),
        "-v", f"{VOLUME}:/opt/oracle/oradata", IMAGE,
    ], check=True)
    print("Wait for DATABASE IS READY TO USE! in docker logs oracle-incident-demo.")


def database_user():
    import oracledb
    from dotenv import dotenv_values
    cfg = dotenv_values(ROOT / ".env")
    assert cfg["ORACLE_MEMORY_DB_USER"] == "incident_demo", "This helper manages only incident_demo."
    password = cfg["ORACLE_MEMORY_DB_PASSWORD"]
    if not password or not password.isalnum():
        raise ValueError("Setup helper requires the generated alphanumeric password.")
    with oracledb.connect(user="system", password=cfg["ORACLE_PWD"],
                          dsn=cfg["ORACLE_MEMORY_DB_CONNECT_STRING"]) as conn:
        with conn.cursor() as cur:
            cur.execute("select tablespace_name from dba_tablespaces where tablespace_name = 'INCIDENT_DEMO_TS'")
            if not cur.fetchone():
                cur.execute("CREATE TABLESPACE incident_demo_ts "
                            "DATAFILE '/opt/oracle/oradata/FREE/FREEPDB1/incident_demo01.dbf' "
                            "SIZE 64M AUTOEXTEND ON NEXT 32M MAXSIZE 500M")
            cur.execute("select username from all_users where username = 'INCIDENT_DEMO'")
            if cur.fetchone():
                print("Dedicated user already exists; keeping its credentials.")
            else:
                cur.execute(f'CREATE USER incident_demo IDENTIFIED BY "{password}"')
            cur.execute("GRANT CREATE SESSION, CREATE TABLE, CREATE SEQUENCE, CREATE VIEW, "
                        "CREATE PROCEDURE, CREATE TRIGGER, CREATE PROPERTY GRAPH, CREATE JOB "
                        "TO incident_demo")
            cur.execute("ALTER USER incident_demo DEFAULT TABLESPACE incident_demo_ts")
            cur.execute("ALTER USER incident_demo QUOTA 500M ON incident_demo_ts")
            print("Dedicated incident_demo user and tablespace ready, with a 500 MB quota.")
            cur.execute("select banner_full from v$version")
            print(cur.fetchone()[0])
    with oracledb.connect(user=cfg["ORACLE_MEMORY_DB_USER"], password=password,
                          dsn=cfg["ORACLE_MEMORY_DB_CONNECT_STRING"]) as conn:
        with conn.cursor() as cur:
            cur.execute("select sys_context('USERENV', 'CON_NAME') from dual")
            print("Application connection verified:", cur.fetchone()[0])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["start", "user"])
    args = parser.parse_args()
    start() if args.action == "start" else database_user()

import datetime
import getpass
import os
import sqlite3
import time
from threading import Thread
import psutil
import winreg
import platform  # Para pegar nome do computador

# === Configurações ===
DATABASE = os.path.expanduser(r"../data/program_usage.db")  # Ajuste conforme seu projeto
LOG_INTERVAL = 60  # segundos

# === Banco de dados ===

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DB")
    )

def init_db() -> None:
    """Inicializa o banco de dados e cria as tabelas necessárias no MySQL."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS program_usage_summary (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user VARCHAR(255) NOT NULL,
                machine_name VARCHAR(255) NOT NULL,
                program_name VARCHAR(255) NOT NULL,
                total_seconds DOUBLE DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_program (user, machine_name, program_name)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS installed_programs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user VARCHAR(255) NOT NULL,
                program_name VARCHAR(255) NOT NULL,
                version VARCHAR(255),
                publisher VARCHAR(255),
                install_location TEXT,
                last_checked TIMESTAMP NOT NULL,
                UNIQUE KEY unique_install (user, program_name)
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Erro ao inicializar banco: {err}")


def update_usage_summary(user: str, machine_name: str, program_name: str, duration: float) -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT total_seconds FROM program_usage_summary 
        WHERE user = %s AND machine_name = %s AND program_name = %s
    """, (user, machine_name, program_name))
    
    row = cur.fetchone()

    if row:
        total = row[0] + duration
        cur.execute("""
            UPDATE program_usage_summary 
            SET total_seconds = %s, last_updated = CURRENT_TIMESTAMP 
            WHERE user = %s AND machine_name = %s AND program_name = %s
        """, (total, user, machine_name, program_name))
    else:
        cur.execute("""
            INSERT INTO program_usage_summary (user, machine_name, program_name, total_seconds, last_updated)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
        """, (user, machine_name, program_name, duration))

    conn.commit()
    cur.close()
    conn.close()


def upsert_installed_program(user: str, program: dict) -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id FROM installed_programs 
        WHERE user = %s AND program_name = %s
    """, (user, program["name"]))
    
    exists = cur.fetchone()
    now = datetime.datetime.now()

    if exists:
        cur.execute("""
            UPDATE installed_programs 
            SET version = %s, publisher = %s, install_location = %s, last_checked = %s 
            WHERE user = %s AND program_name = %s
        """, (
            program["version"], 
            program["publisher"], 
            program["install_location"], 
            now, 
            user, 
            program["name"]
        ))
    else:
        cur.execute("""
            INSERT INTO installed_programs 
            (user, program_name, version, publisher, install_location, last_checked)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            user, 
            program["name"], 
            program["version"], 
            program["publisher"], 
            program["install_location"], 
            now
        ))

    conn.commit()
    cur.close()
    conn.close()


def get_installed_programs() -> list[dict]:
    """Retorna a lista de programas instalados para o usuário atual."""
    programs = []

    reg_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]

    for root, path in reg_paths:
        try:
            key = winreg.OpenKey(root, path)
        except FileNotFoundError:
            continue

        for i in range(winreg.QueryInfoKey(key)[0]):
            try:
                subkey_name = winreg.EnumKey(key, i)
                subkey = winreg.OpenKey(key, subkey_name)

                display_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                try:
                    install_location, _ = winreg.QueryValueEx(subkey, "InstallLocation")
                except FileNotFoundError:
                    install_location = None

                try:
                    publisher, _ = winreg.QueryValueEx(subkey, "Publisher")
                except FileNotFoundError:
                    publisher = None

                try:
                    display_version, _ = winreg.QueryValueEx(subkey, "DisplayVersion")
                except FileNotFoundError:
                    display_version = None

                programs.append({
                    "name": display_name,
                    "version": display_version,
                    "publisher": publisher,
                    "install_location": install_location,
                })

            except FileNotFoundError:
                continue
            except OSError:
                continue

        winreg.CloseKey(key)

    return programs

# === Monitoramento contínuo do uso dos programas ===

active_processes: dict[int, dict] = {}

def monitor_program_usage() -> None:
    user = getpass.getuser()
    machine_name = platform.node()  # Nome do computador (funciona no Windows e Linux)
    print(f"[{datetime.datetime.now()}] Monitorando como usuário: {user} no computador: {machine_name}")

    active_processes.clear()  # limpa para reiniciar

    loop_counter = 0

    while True:
        now = datetime.datetime.now()
        current_pids = set()
        try:
            processos = list(psutil.process_iter(["pid", "name", "username", "create_time"]))
            print(f"[{now}] Loop {loop_counter} - Processos encontrados: {len(processos)}")
            print(f"[{now}] Loop {loop_counter} - Processos ativos armazenados: {len(active_processes)}")

            for proc in processos:
                # Comentando filtro por usuário temporariamente para teste
                # if proc.info["username"] != user:
                #     continue

                pid = proc.info["pid"]
                current_pids.add(pid)

                if pid not in active_processes:
                    start_time = datetime.datetime.fromtimestamp(proc.info["create_time"])
                    active_processes[pid] = {
                        "program_name": proc.info["name"],
                        "start_time": start_time,
                    }
                    print(f"[{now}] Loop {loop_counter} - Novo processo monitorado: {proc.info['name']} (PID {pid})")

            finished_pids = [pid for pid in list(active_processes.keys()) if pid not in current_pids]

            for pid in finished_pids:
                session = active_processes.pop(pid)
                duration = (now - session["start_time"]).total_seconds()
                print(f"[{now}] Loop {loop_counter} - Processo finalizado: {session['program_name']} (PID {pid}), duração {duration:.2f}s")
                update_usage_summary(user, machine_name, session["program_name"], duration)
                print(f"[{now}] Loop {loop_counter} - Uso atualizado no banco para {session['program_name']}")

        except Exception as e:
            print(f"Erro ao iterar processos: {e}")

        loop_counter += 1
        time.sleep(LOG_INTERVAL)

def start_background_monitor() -> Thread:
    thread = Thread(target=monitor_program_usage, daemon=True, name="ProgramUsageMonitor")
    thread.start()
    return thread

# === Função principal ===

def main() -> None:
    print("Iniciando monitoramento contínuo de uso de programas...")
    print(f"Banco de dados: {DATABASE}")

    init_db()

    user = getpass.getuser()
    machine_name = platform.node()

    # Atualiza programas instalados no banco
    programas = get_installed_programs()
    print(f"Foram encontrados {len(programas)} programas instalados. Atualizando banco...")
    for prog in programas:
        upsert_installed_program(user, prog)
    print("Programas instalados atualizados.")

    # Inicia monitoramento contínuo do uso
    start_background_monitor()

    try:
        while True:
            time.sleep(3600)  # Dorme para manter o programa rodando
    except KeyboardInterrupt:
        print("Monitoramento interrompido pelo usuário. Saindo...")

if __name__ == "__main__":
    main()

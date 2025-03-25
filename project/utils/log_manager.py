import os
import datetime


class LogManager:
    log_files = {}

    @staticmethod
    def start_logger(peer_id):
        try:
            log_dir = f"peer_{peer_id}"
            log_file_path = os.path.join(log_dir, f"log_peer_{peer_id}.log")
            os.makedirs(log_dir, exist_ok=True)
            log_file = open(log_file_path, "a")
            LogManager.log_files[peer_id] = log_file
            LogManager.log(peer_id, "Logger initialized successfully.")
        except Exception as e:
            raise RuntimeError(f"Failed to start logger for Peer {peer_id}: {e}")

    @staticmethod
    def log(peer_id, message):
        try:
            if peer_id not in LogManager.log_files:
                raise KeyError(f"Logger for Peer {peer_id} is not initialized.")
            timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
            log_message = f"{timestamp} {message}\n"
            log_file = LogManager.log_files[peer_id]
            log_file.write(log_message)
            log_file.flush()
        except Exception as e:
            print(f"Failed to log message for Peer {peer_id}: {e}")

    @staticmethod
    def close_logger(peer_id):
        try:
            if peer_id in LogManager.log_files:
                log_file = LogManager.log_files.pop(peer_id)
                log_file.close()
        except Exception as e:
            print(f"Failed to close logger for Peer {peer_id}: {e}")

    @staticmethod
    def close_all_loggers():
        try:
            for log_file in LogManager.log_files.values():
                log_file.close()
            LogManager.log_files.clear()
        except Exception as e:
            print(f"Failed to close all loggers: {e}")

    @staticmethod
    def get_log_file(peer_id):
        return f"peer_{peer_id}/log_peer_{peer_id}.log"

    @staticmethod
    def fetch_log_tail(peer_id, num_lines=10):
        try:
            log_file_path = LogManager.get_log_file(peer_id)
            with open(log_file_path, "r") as log_file:
                return log_file.readlines()[-num_lines:]
        except FileNotFoundError:
            return [f"Log file not found for Peer {peer_id}."]
        except Exception as e:
            return [f"Failed to fetch log for Peer {peer_id}: {e}"]

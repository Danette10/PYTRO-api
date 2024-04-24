from network_utils import sio, log_event, attempt_reconnect


def main():
    attempt_reconnect()
    try:
        sio.wait()
    except KeyboardInterrupt:
        log_event("Arrêt du client...")
        sio.disconnect()


if __name__ == '__main__':
    main()

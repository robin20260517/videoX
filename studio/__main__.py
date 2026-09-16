import argparse
import threading
import webbrowser
import uvicorn


def main():
    parser = argparse.ArgumentParser(description='videoX local UGC studio')
    parser.add_argument('--open', action='store_true', help='Open the local studio in your browser')
    args = parser.parse_args()
    if args.open:
        threading.Timer(1.5, lambda: webbrowser.open('http://127.0.0.1:8787')).start()
    uvicorn.run('studio.app:create_app', factory=True, host='127.0.0.1', port=8787, log_level='info')


if __name__ == '__main__':
    main()

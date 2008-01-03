from orbited.config import map as config
from orbited import start

def main():
    if '[plugin:revolved]' not in config:
        config['[plugin:revolved]'] = {}
    config['[plugin:revolved]']['active'] = '1'
    start.main()
    

if __name__ == "__main__":
    start()
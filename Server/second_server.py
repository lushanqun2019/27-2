import sys
import os
from core import src_second

path = os.path.dirname(__file__)
sys.path.append(path)


if __name__ == '__main__':
    src_second.run()

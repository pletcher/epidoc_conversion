import argparse

from src.p6_converter.converter import Converter
from src.p6_converter.converter import preconvert

parser = argparse.ArgumentParser(
                    prog='Epidoc Conversion',
                    description='Script to help with cleaning up Epidoc XML files',
                    epilog='')

parser.add_argument('filename')

if __name__ == '__main__':
    args = parser.parse_args()
    preconvert(args.filename)
    converter = Converter(args.filename)
    converter.convert()

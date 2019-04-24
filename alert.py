#! py -3.7
"""
EXAMPLE SCHEMA:

{'CENADET': 27.99,
 'ECENA': 18.19,
 'EILOSC': 1,
 'EINDEKS': '6102-02-1223119P',
 'ELP': 1,
 'ENAZWA': 'Szko lusterka zewntrznego',
 'ETOW_KOD': 'C18A64',
 'VAT': 23}
 
"""


import typing as t
from dataclasses import dataclass

import unicodedata
import sys
import os
from pprint import pprint
import json
import hashlib
from time import sleep

from win32api import MessageBox
from dbfread import DBF

from directory import DIRECTORY
PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
HASH_DIR = os.path.join(PROJECT_DIR, 'hashes')

MARGE = 0.5

def to_gross(price: float) -> float:
    return round(price * 1.23, 2)

def cleanup(files):
    files = sorted(files, key=lambda file: os.path.getmtime(file))
    for file in files[:-5]:
        print(file, os.path.getmtime(file), 'deleted')
        os.remove(file)

def full_paths(directory, extension):
    return [os.path.join(directory, file) for file in filter(lambda x: x.endswith(extension), os.listdir(directory))]


@dataclass(frozen=True)
class Entry:
    entry: dict
    filename: str

    def __repr__(self):
        return f"[{self.entry['EINDEKS']} - #{self.entry['ENAZWA']}]"

    def __str__(self):
        return self.__repr__()

    @property
    def current_marge(self) -> float:
        return round((self.sell_price - self.buy_price) / self.buy_price, 2)

    @property
    def human_marge(self):
        return f"{int(self.current_marge * 100)}%"
        
    @property
    def buy_price(self) -> float:
        return self.entry['ECENA']

    @property
    def sell_price(self) -> float:
        return self.entry['CENADET']

    @property
    def suggested_price(self) -> float:
        return round(self.entry['ECENA'] + self.entry['ECENA'] * MARGE, 2)

    @property
    def suggested_gross_price(self) -> float:
        return to_gross(self.suggested_price)
    
    @property
    def is_valid(self) -> bool:
        return self.sell_price >= self.suggested_price

    @property
    def hash(self) -> str:
        identifier = f"{self.filename}{os.path.getmtime(self.filename)}{self.entry['EINDEKS']}"
        return str(hashlib.md5(identifier.encode()).hexdigest()) + '.hash'
    
    @property
    def hash_path(self) -> str:
        return os.path.join(HASH_DIR, self.hash)
    
    def disable_warnings(self):
        open(self.hash_path, 'a').close()

    @property
    def is_warned(self):
        return self.hash in os.listdir(HASH_DIR)
        
    def validate(self):
        if not self.is_valid and not self.is_warned:
            alert(
                str(self),
                f"""{self} ma zbyt niska marze: {self.human_marge}

{self.buy_price}zl   <- cena hurtowa 
{self.sell_price}zl  <- obecna cena detaliczna 

{self.suggested_price}zl  <- sugerowana cena
({self.suggested_gross_price}zl  BRUTTO!)"""
                )
            self.disable_warnings()
    
@dataclass
class DBFile:
    path: str
    entries: t.List[Entry] = list
    
    def __post_init__(self):
        self.entries = read_entries(self.path)



def alert(title: str, message: str):
    MessageBox(0, message, title, 0x00001000)
 
def to_unicode(input_data: str) -> str:
    return unicodedata.normalize(u'NFKD', input_data).encode('ascii', 'ignore').decode('utf8')

def dbffiles() -> t.List[str]:
    all_files = filter(lambda x: x.endswith('.dbf'), os.listdir(DIRECTORY))
    full_path_files = [os.path.join(DIRECTORY, file) for file in all_files]

    full_path_files.sort(key=lambda file: os.path.getmtime(file))
    return full_path_files[::-1]

def read_entries(filename: str) -> dict:
    return [Entry(dict(record), filename) for record in DBF(filename, char_decode_errors='ignore')]

def alldbfiles() -> t.List[DBFile]:
    return [DBFile(file) for file in dbffiles()]



def main():
    for file in alldbfiles():
        for entry in file.entries:
            entry.validate()

if __name__ == '__main__':
    print('Dziala!\nPOZOSTAW TO OKNO OTWARTE! \n\nW RAZIE CZEGO SKROT NA PULPICIE to [ALERTY CENOWE]\n\n')
    while True:
        main()
        cleanup(full_paths(HASH_DIR, '.hash'))
        cleanup(full_paths(DIRECTORY, '.dbf'))
        sleep(5)
        
    

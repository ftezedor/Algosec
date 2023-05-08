import warnings, sys, os
import sqlite3

from algosec import Algosec
from common import Input
from support import AlgosecExcel, ReducerHelper
from datetime import datetime
from common import MissingArgumentError
# from reducer import Reducer


warnings.filterwarnings("ignore")

class Database:
    _inst = None

    def __init__(self):
        self._alive = True

        self._rec_counter = 0
        self._rec_limit = 100

        self.m_db  = sqlite3.connect(":memory:")
        #self.m_db  = sqlite3.connect("extractor.db")
        self.m_cur = self.m_db.cursor()

        # self.p_db  = sqlite3.connect("algosec.db")
        # self.p_cur = self.p_db.cursor()

        sql = """
            create table if not exists nwobjects (
                name text,
                ip text
            )
        """

        self.m_cur.executescript(sql)


    def __del__(self):
        if not self._alive: return

        # self.p_cur.close()
        # self.p_db.commit()
        # self.p_db.close()

        self.m_cur.close()
        #self.p_db.commit()
        self.m_db.close()

        self._alive = False

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.__del__()

    def add_nw_ojbect(self, rec):
        sql = "insert into nwobjects (name, ip) values (?, ?)"
        self.m_cur.execute(sql, rec)

    def get_nw_objects(self, name: str):
        self.m_db.commit()
        sql = "select ip from nwobjects where name = ? group by ip"
        rset = self.m_cur.execute(sql, [name]).fetchall()
        return [r[0] for r in rset]

    def add_object(self, rec):
        if self._rec_counter % self._rec_limit == 0:
            self.p_db.commit()
        self._rec_counter += 1

        sql = "insert into objects (id, name, members) values (?, ?, ?)"
        self.p_cur.execute(sql, rec)
        
    def get_object(self, id):
        sql = "select * from objects where id = ?"
        return self.p_cur.execute(sql, [id]).fetchone()

    def add_port(self, rec) -> None:
        if self._rec_counter % self._rec_limit == 0:
            self.p_db.commit()
        self._rec_counter += 1

        sql = "insert into ports (id, name) values (?, ?)"
        self.p_cur.execute(sql, rec)
        
    def get_ports(self, id):
        sql = "select * from ports where id = ?"
        return self.p_cur.execute(sql, [id]).fetchall()

    def close(self):
        self.__del__()

def get_nw_objects(device: str, name: str, db: Database = None):
    nwobjs = []
    if db:
        nwobjs = db.get_nw_objects(name)
        if nwobjs:
            return nwobjs

    print("browsing for {1}@{0}".format(device, name))

    nwobjs = Algosec.get_nw_object(device, name)

    # add to db every IP for the object
    for obj in nwobjs:
        db.add_nw_ojbect([name, obj])
    return nwobjs
    

# search firewall rlues for a given IP address
def search(address: str, excel: AlgosecExcel, db: Database):
    # list to hold rules' numbers to check and void duplicates
    known_fw_rules = []

    # retrieve rules where IP is present in Source
    rules = Algosec.search(address, "Source Address")

    print("Found {0} rule(s) in Source for {1}".format(rules['totalFoundRulesCount'], address))

    if rules['totalFoundRulesCount'] <= 0:
        return

    for dev in rules['devicesFoundBySearch']:
        print("{0} rule(s) from device {1}".format(dev['deviceFoundRulesCount'],  dev['deviceInfo']['displayName']))
        for rule in dev['foundRules']:
            if rule['rule']['enable'] == 'Disabled':
                print(f"-> Rule #{rule['rule']['ruleNum']} is disabled and will be discarded")
                continue

            if rule['rule']['ruleNum'] in known_fw_rules:
                print(f"-> Rule #{rule['rule']['ruleNum']} is already known")
                continue

            known_fw_rules.append(rule['rule']['ruleNum'])

            dst_nw_objs = []
            for obj in rule['rule']['destination']:
                myobjs = get_nw_objects(rule['rule']['deviceDisplayName'], obj["canonizedName"], db)

                for myobj in myobjs:
                    dst_nw_objs.append(myobj)

            excel.add_row([
                rule['rule']['ruleNum'], 
                address,
                '\n'.join([e for e in dst_nw_objs]),
                '\n'.join([e['canonizedName'] for e in rule['rule']['service']]),
                rule['rule']['action'],
                '\n'.join(rule['rule']['comment'])
            ])

    # retrieve rules where IP is present in Destination
    rules = Algosec.search(address, "Destination Address")

    print("Found {0} rule(s) in Destination for {1}".format(rules['totalFoundRulesCount'], address))

    known_fw_rules.clear()
    
    for dev in rules['devicesFoundBySearch']:
        print("{0} rule(s) from device {1}".format(dev['deviceFoundRulesCount'],  dev['deviceInfo']['displayName']))
        for rule in dev['foundRules']:
            if rule['rule']['enable'] == 'Disabled':
                print(f"-> Rule #{rule['rule']['ruleNum']} is disabled and will be discarded")
                continue

            if rule['rule']['ruleNum'] in known_fw_rules:
                print(f"-> Rule #{rule['rule']['ruleNum']} is already known")
                continue

            known_fw_rules.append(rule['rule']['ruleNum'])

            src_nw_objs = []
            for obj in rule['rule']['source']:
                myobjs = get_nw_objects(rule['rule']['deviceDisplayName'], obj["canonizedName"], db)
                for myobj in myobjs:
                    src_nw_objs.append(myobj)

            excel.add_row([
                rule['rule']['ruleNum'], 
                '\n'.join([e for e in src_nw_objs]),
                address,
                '\n'.join([e['canonizedName'] for e in rule['rule']['service']]),
                rule['rule']['action'],
                '\n'.join(rule['rule']['comment'])
            ])


def main(file: str):
    version()
    print("")

    arg1: str = args[0] if len(args) > 0 and args[0] != '' else ""

    if arg1 == '':
        raise MissingArgumentError("The input file is required")

    if not os.path.isfile(arg1):
        raise FileNotFoundError("File {} not found".format(arg1))

    # os.getlogin can throw an exception on linux so let's avoid using it
    #usr_logged = os.getlogin().lower()
    #usr_name = Input.gettext("Enter your username (" + usr_logged + "): ", usr_logged)
    usr_name = Input.gettext("Enter your username: ")
    usr_passwd = Input.getpass("Enter password for " + usr_name + ": ")

    if (usr_name is None or usr_name == '') or (usr_passwd is None or usr_passwd == ''):
        raise ValueError("The username and password are required")

    print("")

    out_file = "algosec_fw_rules_original_" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".xlsx"
    o_file = "original__" + out_file
    r_file = "reduced__" + out_file

    Algosec.login(usr_name, usr_passwd)

    with open(file, "r") as text, AlgosecExcel(o_file) as excel, Database() as db:
        for s_ip_addr in text:
            s_ip_addr = s_ip_addr.strip()
            print(f"Checking '{s_ip_addr}'")
            search(s_ip_addr, excel, db)
            print(f"Done for '{s_ip_addr}'")

    Algosec.logout()

    print(f"\nFile '{o_file}' generated with raw data\n")

    print(f"\nStarting rwa data reduction process\n")

    out_file = ReducerHelper.perform([o_file])

    os.rename(out_file, r_file)

    print(f"check file {r_file}\n")


def help() -> None:
    print("""
    try: extractor.py <option>

    options

        <file_name>   text file 
        --version     print the version
        --help        display this screen
    """)

def version() -> None:
    print("""
    algosec extractor version 1.0.0, May 25, 2022.
    Copyright © 2022 Tezedor. All rights reserved.
    by Fabio Tezedor <fabio@tezedor.com.br>.
    """)

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        help()
        sys.exit(1)

    args = sys.argv[1:]

    for i in range(len(args)):
        if args[i] == "--help" or args[i] == "-h" or args[i] == "/h":
            help()
            break

        if args[i] == "--version" or args[i] == "-v" or args[i] == "/v":
            version()
            break

        main(args[0])

        break

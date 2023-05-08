__author__ = "Fabio Tezedor"
__copyright__ = "Copyright 2021, Tezedor"
__license__ = "Proprietary"
__version__ = "1.0.1"
__maintainer__ = "Fabio Tezedor"
__email__ = "fabio@tezedor.com.br"


import xlsxwriter, xlrd, openpyxl, csv, string
from common import UnknownFormatError

def is_csv(infile):
    try:
        with open(infile, newline='') as csvfile:
            start = csvfile.read(4096)

            # isprintable does not allow newlines, printable does not allow umlauts...
            if not all([c in string.printable or c.isprintable() for c in start]):
                return False
            dialect = csv.Sniffer().sniff(start)
            return True
    except csv.Error:
        # Could not get a csv dialect -> probably not a csv.
        return False

class ExcelWriter:
    def __init__(self, fname: str) -> None:

        self._closed = False

        self._workbook = xlsxwriter.Workbook(fname)
        self._worksheet = self._workbook.add_worksheet()

        self._text_format = self._workbook.add_format({'text_wrap': True,
                                'center_across': True})

        self._row_number = -1

    def __del__(self):
        if self._closed:
            return

        try:
            self._workbook.close()
            self._closed = True
        except Exception as e:
            print(str(e))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback): 
        self.__del__()

    def add_row(self, row: list) -> None:
        if self._closed:
            raise RuntimeError("Object is closed")

        self._row_number += 1

        for col in range(len(row)):
            self._worksheet.write(self._row_number, col, row[col], self._text_format)

    def save(self):
        if self._closed:
            raise RuntimeError("Object is closed")

        self.__del__()



class ExcelReader:
    def __init__(self, fname: str, wsheet: str = None):
        self._ftype = None

        self._matrix = None

        try:
            self.workbook = openpyxl.load_workbook(fname, read_only=False, data_only=True)
            if wsheet == None:
                for s in range(len(self.workbook.sheetnames)):
                    if self.workbook.sheetnames[s] == 'charlie':
                        self.workbook.active = s
                        break
                    #
                #
            #
            self.worksheet = self.workbook.active
            self._ftype = "xlsx"
        except openpyxl.utils.exceptions.InvalidFileException as ex:
            try:
                self.workbook = xlrd.open_workbook(fname)
                if wsheet == None:
                    self.worksheet = self.workbook.sheet_by_index(0)
                else:
                    self.worksheet = self.workbook.sheet_by_name(wsheet)
                self._ftype = "xls"
            except xlrd.biffh.XLRDError as ex:
                if not is_csv(fname):
                    raise UnknownFormatError(f"File {fname} is not a .xls, .xlsx or .csv file")
                with open(fname, mode='r', encoding="ISO-8859-1") as csv_file:
                    csv_reader = csv.reader(csv_file, delimiter=',')
                    self._matrix = [row for row in csv_reader]
                #
                self._ftype = "csv"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback): 
        self.__del__()

    def __del__(self):
        pass

    def read_all(self) -> list:
        if self._ftype == "xls":
            return self._xlrd_read_all()
        elif self._ftype == "xlsx":
            return self._pyxl_read_all()
        else:
            return self._csv_read_all()

    def _csv_read_all(self):
        return self._matrix

    def _pyxl_read_all(self):
        if self._matrix == None:
            self._matrix = [r for r in self.worksheet.values] 
        return self._matrix

    def _xlrd_read_all(self):
        if self._matrix != None:
            return self._matrix

        num_rows = self.worksheet.nrows - 1
        num_cells = self.worksheet.ncols - 1

        self._matrix = [ ['']*self.worksheet.ncols for i in range(self.worksheet.nrows) ]

        curr_row = -1
        while curr_row < num_rows:
            curr_row += 1
            curr_cell = -1
            while curr_cell < num_cells:
                curr_cell += 1
                cell_value = self.worksheet.cell_value(curr_row, curr_cell)
                self._matrix[curr_row][curr_cell] = str(cell_value)
        
        return self._matrix

if __name__ == '__main__':
    excel = ExcelReader('contoso.csv')

    print(excel.read_all()[2])
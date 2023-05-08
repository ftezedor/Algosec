import sys, os
from excel import ExcelWriter, ExcelReader
from reducer import Reducer
from common import MissingArgumentError, Timer

class AlgosecExcel(ExcelWriter):
    """
    This class inherits from ExcelWriter \n
    Some formatting has been added in order \n
    to get the desired algosec report presentation
    """
    def __init__(self, fname: str) -> None:
        ExcelWriter.__init__(self, fname)

        self._worksheet.set_column('A:G', 20)

        # Formattings

        header = self._workbook.add_format({'bold': True,
                                    'text_wrap': True,
                                    'center_across': True})

        header.set_align('justify')
        header.set_align('vjustify')
        header.set_align('center')
        header.set_align('vcenter')

        ipformat = self._workbook.add_format({'underline': True,
                                        'italic': True,
                                        'center_across': True})

        ipformat.set_align('justify')
        ipformat.set_align('vjustify')
        ipformat.set_align('center')
        ipformat.set_align('vcenter')

        self._text_format = self._workbook.add_format({'text_wrap': True,
                                        'center_across': True})

        self._text_format.set_align('justify')
        self._text_format.set_align('vjustify')
        self._text_format.set_align('center')
        self._text_format.set_align('vcenter')

        # End of Formattings

        # HEADER
        self._worksheet.write('A1', "Rule #", header)
        self._worksheet.write('B1', "Source Network", header)
        self._worksheet.write('C1', "Destination Network", header)
        self._worksheet.write('D1', "Destination Service", header)
        self._worksheet.write('E1', "Action", header)
        self._worksheet.write('F1', "Comment Group", header)

        # since the header just got added, the row number must be increased
        self._row_number += 1



class ReducerHelper:
    @classmethod
    def add_category(cls, args: list):
        if isinstance(args, tuple):
            lst = list(args)
            lst.insert(1, "0")
            args = tuple(lst)
        elif isinstance(args, list):
            args.insert(1, "0")
        else:
            raise TypeError(f"A list or tuple is expected rather than a {type(args)}")
        
        return args


    @classmethod
    def normalize(cls, args: list):
        for arg in args:
            if arg is None or arg == "None":
                arg = ""

        # return args
        return list(map(lambda x: x.replace(";","\n"), args))

    @classmethod
    def handle(cls, args: list):
        for arg in args[::-1]:
            if arg == "--help" or arg == "-h":
                cls.help()
                return
            if arg == "--version" or arg == "-v":
                Reducer.version()
                return
        #
        cls.perform(args)
    #

    @classmethod
    def perform(cls, args: list):

            fname = None if args == None or args == [] else args[0]

            if fname == None or fname == '':
                raise MissingArgumentError("The input file is required")

            if not os.path.isfile(fname):
                raise FileNotFoundError("File {} not found".format(fname))

            matrix = []

            with ExcelReader(fname) as excel:
                matrix = excel.read_all()

            row_counter = 0
            bad_rows = 0

            for idx in range(len(matrix)):
                row_counter += 1
                # if row has only 6 columns we assume that the rule category (column B) 
                # is missing and then the value '0' is inserted
                if len(matrix[idx]) == 6: 
                    matrix[idx] = cls.add_category(matrix[idx])

                if len(matrix[idx]) != 7:
                    bad_rows += 1
                    print(f"Row #{row_counter} does not have exactly 7 columns")
            
            if bad_rows > 0:
                raise RuntimeError(f"File {fname} is not well formatted")

            print(f"\nNumber of rows loaded from {fname}: {len(matrix)}\n")

            recs = len(matrix)
            loops = 0

            oTimer = Timer()

            sort_names = ['source', 'destination', 'port']

            for i in 1, 2, 3:
                oTimer.start()

                if i == 1:
                    matrix = sorted(matrix, key=lambda x: (x[1], x[2], x[3], x[4]))
                elif i == 2:
                    matrix = sorted(matrix, key=lambda x: (x[1], x[4], x[2], x[3]))
                else:
                    matrix = sorted(matrix, key=lambda x: (x[1], x[3], x[4], x[2]))    

                recs = recs = len(matrix)
                loops = 0

                while True:
                    loops += 1
                    matrix = Reducer.reduce(matrix)
                    if not (recs == -1 or recs != len(matrix)):
                        break
                    else:
                        recs = len(matrix)

                oTimer.stop()

                print(f"sorted by column {sort_names[i-1]}: reduction steps taken: {loops}, elapsed time: {oTimer.elapsed():.5f} seconds, resulting rows: {len(matrix)}")

            print(f"\nNumber of rows after reduction: {len(matrix)}\n")
 
            ofile = "reduced_" + os.path.basename(fname).split(".")[0] + ".xlsx"

            with AlgosecExcel(ofile) as excel:
                for m in matrix:
                    if isinstance(m, list):
                        #print(",".join(m))
                        excel.add_row(cls.normalize((m[0],m[2],m[3],m[4],m[5],m[6])))
                    else:
                        print("not a list")
                    #
                #
            #

            return ofile

        #
    #end perform()

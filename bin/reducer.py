class Reducer:
    @classmethod
    def clear(cls, matrix: list) -> None:
        """
        cleans up the given matrix (2 dimensional array)
        """
        for m in matrix:
            if isinstance(matrix[m], set):
                matrix[m].clear()
            elif isinstance(matrix[m], list):
                matrix[m].clear()
            elif isinstance(matrix[m], str):
                matrix[m] = ""
            else:
                print(type(matrix[m]))
                raise Exception("cannot clear the object")

    @classmethod
    def load_A(cls, accumulator: dict, data: list):
        accumulator['I'].add(str(data[0]))
        accumulator['K'] = str(data[1])
        accumulator['S'].add(str(data[2]))
        accumulator['D'].add(str(data[3]))
        accumulator['P'].add(str(data[4]))
        accumulator['T'].add(str(data[5]))
        accumulator['C'].add(str(data[6]))

    @classmethod 
    def standardize(cls, cell: list) -> str:
        """
        1 - sort
        2 - remove blank
        3 - remove duplicates
        """
        tmp = ';'.join(cell).split(";")
        tmp.sort()
        return ';'.join(set(filter(None, tmp)))

    @classmethod
    def unload_A(cls, accumulator: dict) -> list:
        """
        pack up the data from the accumulator into a list and gives it back 
        additionally, clean up the accumulator
        """
        r = [
            cls.standardize(accumulator['I']),
            accumulator['K'],
            cls.standardize(accumulator['S']),
            cls.standardize(accumulator['D']),
            cls.standardize(accumulator['P']),
            cls.standardize(accumulator['T']),
            # this must be treated differently
            '\n'.join(set(filter(None, accumulator['C'])))
        ]

        cls.clear(accumulator)
        return r

    @classmethod
    def reduce(cls, lst: list) -> list:
        """
        takes a matrix of 7 x N and groups the rows that match \n
        the matrix must be sorted out by either columns 1 (category) and 2 (source) or 1 and 3 (dest) or 1 and 4 (port) \n\n
        id | category | source  | destiation | port | action | notes \n
        ---+----------+---------+------------+------+--------+----------- \n
         1 |     0    | 1.1.1.1 | 2.2.2.2    |  80  | Accept | OIOIOIOIO \n
        ---+----------+---------+------------+------+--------+----------- \n
         2 |     2    | 1.1.1.1 | 1.2.3.4    |  80  | Accept | \n
        ---+----------+---------+------------+------+--------+-----------
        """

        if not isinstance(lst, list):
            raise TypeError(f"A list is expected but {type(lst)} was found")  

        # holds the resulting reduced matrix
        R = []
        # holds up the previous row of the matrix
        W = None
        # the accumulator itself
        A = {
            "I": set([]),   # id
            "K": "",        # category (kategory ;-D)
            "S": set([]),   # source
            "D": set([]),   # destination
            "P": set([]),   # port (or protocol)
            "T": set([]),   # rule type (action)
            "C": set([])    # comment/note/observation
        }

        for m in lst:
            if not (isinstance(m, list) or isinstance(m, tuple)):
                raise TypeError(f"A list is expected but {type(m)} was found")

            if len(m) < 7 or len(m) > 8:
                raise ValueError(f"A record of 7 or 8 fields is expected but {len(m)} was found")
                #raise ValueError(f"A 7 item list is expected but {len(m)} was found")

            K = m[1]
            S = m[2]
            D = m[3]
            P = m[4]

            # first round? 
            # updates W and A with the current row's data
            # and go to the top of the loop for the next row
            if W == None:
                W = [K, S, D, P]
                cls.load_A(A, m)

                continue

            # in case of duplicate data, ignore it
            if W[0] == K and W[1] == S and W[2] == D and W[3] == P:
                continue

            #
            #  it is here that the magic takes place
            #
            # = = !
            # only P differs so adds it to A['P']
            if W[0] == K and W[1] == S and W[2] == D and W[3] != P:
                A['P'].add(P)
            # = ! =
            # only D differs so adds it to A['D']
            #elif W[0] == S and W[1] != D and W[2] == P and W[3] == K:
            elif W[0] == K and W[1] == S and W[2] != D and W[3] == P:
                A['D'].add(D)
            # ! = =
            # only S differs so adds it to A['S']
            #elif W[0] != S and W[1] == D and W[2] == P and W[3] == K:
            elif W[0] == K and W[1] != S and W[2] == D and W[3] == P:
                A['S'].add(S)
            # more than one different column 
            # updates R with the accumulated data so far
            # and restarts the accumulator with the current row's data
            else:
                R.append(cls.unload_A(A))
                cls.load_A(A, m)

            # updates W with the current row's data
            W = [K, S, D, P]

        R.append(cls.unload_A(A))

        return R

    #end reduce

    @classmethod
    def sort_reduce(cls, lst: list) -> list:
        """
        takes a matrix of 7 x N and groups the rows that matches \n
        the matrix must be sorted out by either columns 1 (category), 2 (source), 3 (dest) or 4 (port) \n
        it sorts the matrix in 3 different ways and reduces it until it can not be reduced any further
        """

        #for i in 0, 1, 2, 3:
        for i in 1, 2, 3:
            if i == 1:
                lst = sorted(lst, key=lambda x: (x[1], x[2], x[3], x[4]))
            elif i == 2:
                lst = sorted(lst, key=lambda x: (x[1], x[4], x[2], x[3]))
            elif i == 3:
                lst = sorted(lst, key=lambda x: (x[1], x[3], x[4], x[2]))  

            recs = len(lst)

            while True:
                lst = Reducer.reduce(lst)
                if not (recs == -1 or recs != len(lst)):
                    break
                else:
                    recs = len(lst)
        
        return lst
    #end sort_reduce

    @classmethod
    def version(cls) -> None:
        print("""
        reducer version 1.1.0, December 1, 2021.
        Copyright © 2021 Tezedor. All rights reserved.
        by Fabio Tezedor <fabio@tezedor.com.br>.
        """)

#end class

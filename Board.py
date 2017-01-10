import unicodedata


class Board:

    def __init__(self, board=None, size=8):

        assert size >= 4 and size % 2 == 0
        self.size = size

        # Check for the different types of input.

        if board is None:
            self.generate_initial_board()

        elif isinstance(board, str):
            self.board = list(map(list, self.convert_board(self.size, board)))

        elif all(isinstance(elem, str) for elem in board):
            self.board = list(map(list, board))

        elif all(isinstance(elem, unicode) for elem in board):
            def uni_to_str(u):
                return unicodedata.normalize('NFKD', u).encode('ascii', 'ignore')
            self.board = list(map(lambda u: list(uni_to_str(u)), board))

        elif all(isinstance(elem, list) for elem in board):
            self.board = board

    def __getitem__(self, item):
        i, j = item
        return self.board[i][j]

    def __setitem__(self, key, value):
        k1, k2 = key
        self.board[k1][k2] = value

    @staticmethod
    def convert_board(size, board):
        board = board.replace('\n', '')
        board = board.replace(' ', '')
        return [board[i:i + size] for i in range(0, len(board), size)]

    def generate_initial_board(self):
        self.board = self.convert_board(self.size,
                                        """_b_b_b_b
                                        b_b_b_b_
                                        ___b_b_b
                                        b_______
                                        ________
                                        w_w_w_w_
                                        _w_w_w_w
                                        w_w_w_w_""")

    def is_inbound(self, position):
        if position[0] < 0 or position[0] >= len(self.board):
            return False
        if position[1] < 0 or position[1] >= len(self.board[0]):
            return False
        return True

    def get_size(self):
        return self.size

    def get_board(self):
        return self.board

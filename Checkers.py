import copy


class Checkers:

    def __init__(self, size=8):

        # TODO: Add board to constructor?
        self.size = size
        self.game_over = False
        self.winner = None
        self.shift_count = 0  # Non-capturing move count.

    @staticmethod
    def opponent(color):

        return "b" if color.lower() == "w" else "w"

    def update_shift_count(self, move):
        if len(move) == 2:
            self.shift_count += 1
        else:
            self.shift_count = 0

    @staticmethod
    def shifts(board, pos, king=False, north=False):
        assert board.is_inbound(pos), "Shift: the disc is not on the board."

        # Direction of play.
        game_direction = [pow(-1, north)] + [pow(-1, not north)] * king

        moves = []

        # Check if any 1st-tier/direct neighboring positions are free.
        for i in game_direction:
            for j in xrange(-1, 2, 2):
                free = (pos[0] + i, pos[1] + j)  # Free position

                if board.is_inbound(free) and board[free] == "_":
                    moves.append([pos, free])

        return moves

    @staticmethod
    def single_jumps(board, pos, king=False, north=False):
        assert board.is_inbound(pos), "Single jump: the disc is not on the board."

        game_direction = [pow(-1, north)] + [pow(-1, not north)] * king
        allowed_positions = []

        for i in game_direction:
            for j in xrange(-1, 2, 2):
                oppo = (pos[0] + i, pos[1] + j)  # Opponent position
                free = (pos[0] + 2 * i, pos[1] + 2 * j)  # Free position

                if board.is_inbound(free) and board[free] == "_" \
                        and board[oppo].lower() not in [board[pos].lower(), "_"]:
                    allowed_positions.append(free)

        return allowed_positions

    def jumps(self, board, pos, jump, moves, king=False, north=False):
        s_jumps = self.single_jumps(board, pos, king, north)

        # End of recursion: here, no new jumps are available.
        if len(s_jumps) == 0 and len(jump) > 1:

            # If we land on the exact same position,
            # pop the last jump out of the move.

            if jump[-1] == jump[0]:
                jump.pop()

            # Check if jump is a sub-jump of an existing move.
            # For this, we convert jumps to strings.

            jump_as_string = ''.join(map(str, jump))
            if all(jump_as_string not in ''.join(map(str, s)) for s in moves):
                moves.append(jump)
            return

        for new_pos in s_jumps:

            new_board = copy.deepcopy(board)
            new_jump = jump + [new_pos]
            new_king = king

            # If the disc reaches the opponent's board side, crown it.
            if (north and new_pos[0] == 0) or (not north and new_pos[0] == board.size - 1):
                new_king = True

            self.update_board_single(new_board, pos, new_pos)
            self.jumps(new_board, new_pos, new_jump, moves, new_king, north)

    def allowed_moves(self, game_state):
        board, color = game_state
        north = color == "w"

        disc_positions = []
        for i, row in enumerate(board.get_board()):
            for j, char in enumerate(row):
                if char.lower() == color:
                    disc_positions.append((i, j))

        moves = []

        for p in disc_positions:
            king = board[p].istitle()
            jump = [p]
            self.jumps(board, p, jump, moves, king, north)

        if len(moves) == 0:

            # Here, no capturing moves have been added.
            # We can thus start to suggest shifts.

            for p in disc_positions:
                king = board[p].istitle()
                moves.extend(self.shifts(board, p, king, north))

        return moves

    @staticmethod
    def update_board_single(board, position, new_position):
        pos, new = position, new_position

        assert abs(pos[0] - new[0]) < 3, "The suggested shift cannot be performed by a legal move."
        assert board.is_inbound(new), "The new position is not on the board."

        # Non-capturing action
        if abs(pos[0] - new[0]) == 1:

            assert board[new] == "_"
            board[new] = board[pos]
            board[pos] = "_"

        # Capturing action
        elif abs(pos[0] - new[0]) == 2:

            # Position of the captured disc.
            capt = ((new[0] + pos[0]) / 2, (new[1] + pos[1]) / 2)

            assert board[new] == "_"
            assert board[capt].lower() not in [board[pos].lower(), "_"]

            board[new] = board[pos]
            board[capt] = board[pos] = "_"

    def update_board(self, game_state, move):

        board = game_state[0]
        for i in xrange(len(move) - 1):
            self.update_board_single(board, move[i], move[i + 1])

        game_state = (board, self.opponent(game_state[1]))
        return game_state

    def end_game(self, game_state):

        """
        Returns the winner.
        :param game_state:
        :return:
        """

        if len(self.allowed_moves(game_state)) == 0:
            return self.opponent(game_state[1])

        elif len(self.allowed_moves((game_state[0], self.opponent(game_state[1])))) == 0:
            return game_state[1]

        elif self.shift_count >= 40:
            return "draw"

        else:
            return None

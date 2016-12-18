import time
import random
import math
import copy
from Board import Board
from Checkers import Checkers


class MonteCarloAgent:

    def __init__(self, checkers, color, **kwargs):
        self.color = color
        self.checkers = checkers
        self.sim_time = kwargs.get('sim_time', 5)
        self.state_node = {}

    def static_concentric_val(self, game_state, king_coefficient=20):

        def concentric_coefficient(b, pos):

            if pos[0] == 0 or pos[0] == len(b.get_board()) - 1:
                return 5
            elif pos[1] == 0 or pos[1] == len(b.get_board()[0]) - 1:
                return 4
            elif (pos[0] == 1 or pos[0] == 6) and (pos[1] <= 6 or pos[1] >= 1):
                return 3
            elif (pos[1] == 1 or pos[1] == 6) and (pos[0] <= 6 or pos[0] >= 1):
                return 3
            elif (pos[0] == 2 or pos[0] == 5) and (pos[1] <= 5 or pos[1] >= 2):
                return 2
            elif (pos[1] == 2 or pos[1] == 5) and (pos[0] <= 5 or pos[0] >= 2):
                return 2
            else:
                return 1

        # Count the number of discs of the player's color,
        # and reward for kings. Subtract the opponent toll.

        board, color = game_state

        play = 0
        oppo = 0

        for i, row in enumerate(board.get_board()):
            for j, char in enumerate(row):
                if char == color.lower():
                    play += 3 + concentric_coefficient(board, (i, j))
                if char == color.upper():
                    play += king_coefficient

                if char == self.checkers.opponent(color).lower():
                    oppo += 3 + concentric_coefficient(board, (i, j))
                if char == self.checkers.opponent(color).upper():
                    oppo += king_coefficient

        return play - oppo

    def play(self, game_state):
        play = self.monte_carlo_search(game_state)
        self.checkers.update_shift_count(play)
        return play

    def monte_carlo_search(self, game_state):

        """
        Returns best action w. Monte-Carlo Tree Search + Upper Confidence Bound.
        :param game_state:
        :return:
        """

        results = {}

        if game_state in self.state_node:
            root = self.state_node[game_state]
        else:
            n_children = len(self.checkers.allowed_moves(game_state))
            root = Node(game_state, None, n_children)

        # even if this is a "recycled" node we've already used,
        # remove its parent as it is now considered our root level node
        root.parent = None

        sim_count = 0
        now = time.time()
        while time.time() - now < self.sim_time and root.moves_unfinished > 0:
            picked_node = self.tree_policy(root)
            result = self.simulate(picked_node.game_state)
            self.back_prop(picked_node, result)
            sim_count += 1

        for child in root.children:
            wins, plays = child.get_wins_plays()
            position = child.move

            results[tuple(position)] = (wins, plays)

        for position in sorted(results, key=lambda x: results[x][1]):
            print('{}: ({}/{})'.format(position, results[position][0], results[position][1]))
        print('{} simulations performed.'.format(sim_count))
        return self.best_action(root)

    @staticmethod
    def best_action(node):

        """Returns the best action from this game state node.
        In Monte Carlo Tree Search we pick the one that was
        visited the most.  We can break ties by picking
        the state that won the most."""

        most_plays = -float('inf')
        best_wins = -float('inf')
        best_actions = []
        for child in node.children:
            wins, plays = child.get_wins_plays()

            if plays > most_plays:
                most_plays = plays
                best_actions = [child.move]
                best_wins = wins
            elif plays == most_plays:
                # break ties with wins
                if wins > best_wins:
                    best_wins = wins
                    best_actions = [child.move]
                elif wins == best_wins:
                    best_actions.append(child.move)

        return random.choice(best_actions)

    @staticmethod
    def back_prop(node, delta):
        """Given a node and a delta value for wins,
        propagate that information up the tree to the root."""
        while node.parent is not None:
            node.plays += 1
            node.wins += delta
            node = node.parent

        # update root node of entire tree
        node.plays += 1
        node.wins += delta

    def tree_policy(self, root):
        """Given a root node, determine which child to visit
        using Upper Confidence Bound."""
        cur_node = root

        while True and root.moves_unfinished > 0:

            # TODO: use end_game?
            legal_moves = self.checkers.allowed_moves(cur_node.game_state)

            if self.checkers.end_game(cur_node.game_state) is not None:
                # the game is won
                cur_node.propagate_completion()
                return cur_node

            elif len(cur_node.children) < len(legal_moves):
                # children are not fully expanded, so expand one
                unexpanded = [
                    move for move in legal_moves
                    if tuple(move) not in cur_node.moves_expanded
                ]

                assert len(unexpanded) > 0
                move = random.choice(unexpanded)

                next_state = copy.deepcopy(cur_node.game_state)
                next_state = self.checkers.update_board(next_state, move)

                child = Node(next_state, move, len(legal_moves))
                cur_node.add_child(child)
                self.state_node[next_state] = child

                return child

            else:
                # Every possible next state has been expanded, so pick one
                cur_node = self.best_child(cur_node)

        return cur_node

    def best_child(self, node):
        enemy_turn = (node.game_state[1] != self.color)

        c = 1  # 'exploration' value
        values = {}
        for child in node.children:
            wins, plays = child.get_wins_plays()

            if enemy_turn:
                # the enemy will play against us, not for us
                wins = plays - wins
            _, parent_plays = node.get_wins_plays()

            assert parent_plays > 0

            values[child] = (wins / plays) \
                + c * math.sqrt(2 * math.log(parent_plays) / plays)

        best_choice = max(values, key=values.get)
        return best_choice

    def simulate(self, game_state):

        """Starting from the given board, simulate
        a random game to completion, and return the profit value
        (1 for a win, 0.5 for a draw, 0 for a loss)"""

        state = copy.deepcopy(game_state)
        checkers_copy = copy.deepcopy(self.checkers)

        while True:
            result = checkers_copy.end_game(state)
            if result is not None:

                # for s in map(lambda r: "".join(r), state[0].get_board()):
                #    print s
                # print

                print "Game over!", result
                if result == self.color:
                    return 1
                elif result == checkers_copy.opponent(self.color):
                    return 0
                elif result == "draw":
                    return .5
                else:
                    raise ValueError

            moves = checkers_copy.allowed_moves(state)

            # Light playout w/ scoring function + epsilon-greedy pick.
            best_score = -float("inf")
            best_move = None
            epsilon = .0

            for current_move in moves:
                state_to_score = copy.deepcopy(state)
                state_to_score = checkers_copy.update_board(state_to_score, current_move)

                current_score = self.static_concentric_val(state_to_score)

                if current_score > best_score:
                    best_move = current_move
                    best_score = current_score

            probability = random.random()
            if probability < epsilon:
                picked = best_move
            else:
                picked = random.choice(moves)

            # for s in map(lambda r: "".join(r), state[0].get_board()):
            #    print s
            # print

            state = checkers_copy.update_board(state, picked)
            checkers_copy.update_shift_count(picked)


class Node:

    def __init__(self, game_state, move, amount_children):
        self.game_state = game_state
        self.plays = 0
        self.wins = 0
        self.children = []
        self.parent = None
        self.moves_expanded = set()  # which moves have we tried at least once
        self.moves_unfinished = amount_children  # amount of moves not fully expanded

        # the move that led to this child state
        self.move = move

    def propagate_completion(self):
        """
        If all children of this move have each been expanded to
        completion, tell the parent that it has one fewer children
        left to expand.
        """
        if self.parent is None:
            return

        if self.moves_unfinished > 0:
            self.moves_unfinished -= 1

        self.parent.propagate_completion()

    def add_child(self, node):
        self.children.append(node)
        self.moves_expanded.add(tuple(node.move))
        node.parent = self

    def has_children(self):
        return len(self.children) > 0

    def get_wins_plays(self):
        return self.wins, self.plays

if __name__ == "__main__":

    hacker_rank = False

    if not hacker_rank:

        that_color = "b"
        that_size = 8

        that_board = [
            '________',
            '__b_____',
            '_w_w____',
            '________',
            '_w______',
            '______b_',
            '_____w__',
            '____w___'
        ]

    else:

        that_color = raw_input()
        that_size = int(raw_input())

        that_board = []
        for k in xrange(that_size):
            that_board.append(raw_input())

    that_board = Board(that_board)
    that_checkers = Checkers()

    agent = MonteCarloAgent(that_checkers, that_color, **{"sim_time": 5})
    that_move = agent.play((that_board, that_color))

    print(len(that_move) - 1)
    for coord in that_move:
        print coord[0], coord[1]

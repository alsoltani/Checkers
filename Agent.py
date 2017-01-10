import time
import random
import math
import copy


class MonteCarloAgent:

    def __init__(self, checkers, color, sim_time=5, c=1, b=0.1):
        self.color = color
        self.checkers = checkers
        self.sim_time = sim_time  # Simulation time
        self.state_node = {}  # Game state tree
        self.c = c  # Exploration value
        self.b = b  # Pre-tuned bias constant

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

        # Remove its parent as it is now considered our root level node.

        root.parent = None

        sim_count = 0
        now = time.time()
        while time.time() - now < self.sim_time and root.moves_unfinished > 0:
            picked_node = self.tree_policy(root)
            result, actions = self.simulate(picked_node.game_state)
            self.back_prop(picked_node, result, actions, player=picked_node.game_state[1])
            sim_count += 1

        for child in root.children:
            wins, plays = child.get_wins_plays()
            position = child.move

            results[tuple(position)] = (wins, plays)
        return self.best_action(root)

    @staticmethod
    def best_action(node):

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
    def back_prop(node, delta, actions, player):

        t = 0
        while node.parent is not None:
            node.plays += 1
            node.wins += delta

            for u in xrange(t, len(actions[player])):
                if actions[player][u] not in actions[player][t:u]:
                    node.amaf_plays += 1
                    node.amaf_wins += delta

            t += 1
            node = node.parent

        # Update root node of entire tree.

        node.plays += 1
        node.wins += delta

        for u in xrange(t, len(actions[player])):
            if actions[player][u] not in actions[player][t:u]:
                node.amaf_plays += 1
                node.amaf_wins += delta

    def tree_policy(self, root):

        """
        Given a root node, determine which child to visit
        using Upper Confidence Bound.
        """

        cur_node = root

        while True and root.moves_unfinished > 0:

            legal_moves = self.checkers.allowed_moves(cur_node.game_state)

            if self.checkers.end_game(cur_node.game_state) is not None:
                # Game is over.
                cur_node.propagate_completion()
                return cur_node

            elif len(cur_node.children) < len(legal_moves):

                # Children are not fully expanded, expand one.
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
                # Every possible next state has been expanded, pick one.
                cur_node = self.best_child(cur_node)

        return cur_node

    def best_child(self, node):

        enemy_turn = (node.game_state[1] != self.color)
        values = {}

        for child in node.children:
            wins, plays = child.get_wins_plays()
            a_wins, a_plays = child.get_amaf_wins_plays()

            if enemy_turn:
                wins = plays - wins
                a_wins = a_plays - a_wins

            _, parent_plays = node.get_wins_plays()
            beta = node.get_beta(self.b)

            if a_plays > 0:
                values[child] = (1 - beta) * (wins / plays) + beta * (a_wins / a_plays) \
                    + self.c * math.sqrt(2 * math.log(parent_plays) / plays)
            else:
                values[child] = (wins / plays) + \
                                self.c * math.sqrt(2 * math.log(parent_plays) / plays)

        best_choice = max(values, key=values.get)
        return best_choice

    def simulate(self, game_state):

        """Starting from the given board, simulate
        a random game to completion, and return the profit value
        (1 for a win, 0.5 for a draw, 0 for a loss)"""

        actions = {game_state[1]: [], self.checkers.opponent(game_state[1]): []}

        state = copy.deepcopy(game_state)
        checkers_copy = copy.deepcopy(self.checkers)

        while True:
            result = checkers_copy.end_game(state)
            if result is not None:

                if result == self.color:
                    return 1, actions
                elif result == checkers_copy.opponent(self.color):
                    return 0, actions
                elif result == "draw":
                    return .5, actions
                else:
                    raise ValueError

            moves = checkers_copy.allowed_moves(state)
            picked = random.choice(moves)
            actions[state[1]].append(picked)

            state = checkers_copy.update_board(state, picked)
            checkers_copy.update_shift_count(picked)


class Node:

    def __init__(self, game_state, move, amount_children):

        # TODO: Use heuristic for Q, N initialization?
        self.game_state = game_state
        self.plays = 10
        self.wins = 0.5
        self.amaf_plays = 10
        self.amaf_wins = 0.5
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

    def get_amaf_wins_plays(self):
        return self.amaf_wins, self.amaf_plays

    def get_beta(self, b):
        return self. amaf_plays / (self.plays + self.amaf_plays +
                                   4 * self.plays * self.amaf_plays * pow(b, 2))

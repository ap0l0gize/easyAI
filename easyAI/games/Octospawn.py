from easyAI import TwoPlayerGame
import random

# Convert D7 to (3,6) and back...
to_string = lambda move: " ".join(
    ["ABCDEFGHIJ"[move[i][0]] + str(move[i][1] + 1) for i in (0, 1)]
)
to_tuple = lambda s: ("ABCDEFGHIJ".index(s[0]), int(s[1:]) - 1)


class Hexapawn(TwoPlayerGame):
    """
    A nice game whose rules are explained here:
    http://fr.wikipedia.org/wiki/Hexapawn
    """

    def __init__(self, players, size=(4, 4)):
        self.size = M, N = size
        p = [[(i, j) for j in range(N)] for i in [0, M - 1]]

        for i, d, goal, pawns in [(0, 1, M - 1, p[0]), (1, -1, 0, p[1])]:
            players[i].direction = d
            players[i].goal_line = goal
            players[i].pawns = pawns

        self.players = players
        self.current_player = random.choice([1,2]) # randomly choose player 1 or 2 to start the game

    def possible_moves(self):
        moves = []
        opponent_pawns = self.opponent.pawns
        d = self.player.direction
        for i, j in self.player.pawns:
            if (i + d, j) not in opponent_pawns:
                moves.append(((i, j), (i + d, j)))
            if (i + d, j + 1) in opponent_pawns:
                moves.append(((i, j), (i + d, j + 1)))
            if (i + d, j - 1) in opponent_pawns:
                moves.append(((i, j), (i + d, j - 1)))

        return list(map(to_string, [(i, j) for i, j in moves]))

    def make_move(self, move):
        move = list(map(to_tuple, move.split(" ")))
        ind = self.player.pawns.index(move[0])
        self.player.pawns[ind] = move[1]

        if move[1] in self.opponent.pawns:
            # capturing pawns after move
            if not hasattr(self.player, "captured_pawns"):
                self.player.captured_pawns = []
            col = move[1][1]
            start_row = self.opponent.goal_line
            start_pos = (start_row, col)

            self.player.captured_pawns.append(start_pos)
            self.opponent.pawns.remove(move[1])

        # probabilistic variant, comment if needed
        if hasattr(self.player, "captured_pawns") and self.player.captured_pawns:
            # 10% chance
            if random.random() < 0.1:
                respawn_pos = random.choice(self.player.captured_pawns)

                # print("Trying respawn at:", respawn_pos)

                if respawn_pos not in self.player.pawns and respawn_pos not in self.opponent.pawns:
                    # print("Respawned at:", respawn_pos)
                    self.player.pawns.append(respawn_pos)
                    self.player.captured_pawns.remove(respawn_pos)

    def lose(self):
        return any([i == self.opponent.goal_line for i, j in self.opponent.pawns]) or (
            self.possible_moves() == []
        )

    def is_over(self):
        return self.lose()

    def show(self):
        f = (
            lambda x: "1"
            if x in self.players[0].pawns
            else ("2" if x in self.players[1].pawns else ".")
        )
        print(
            "\n".join(
                [
                    " ".join([f((i, j)) for j in range(self.size[1])])
                    for i in range(self.size[0])
                ]
            )
        )


if __name__ == "__main__":
    from easyAI import AI_Player, Human_Player, Negamax

    # dicts to calculate wins
    shallow_wins = {"1": 0, "2": 0}
    deep_wins = {"1": 0, "2": 0}

    # more shallow search (8 moves ahead)
    for i in range(10):
        scoring = lambda game: -100 if game.lose() else 0
        ai = Negamax(8, scoring)
        game = Hexapawn([AI_Player(ai), AI_Player(ai)])
        game.play()
        shallow_wins[str(game.opponent_index)] += 1
        # print("player %d wins after %d turns " % (game.opponent_index, game.nmove))

    # deeper searching (13 moves ahead)
    for i in range(10):
        scoring = lambda game: -100 if game.lose() else 0
        ai = Negamax(13, scoring)
        game = Hexapawn([AI_Player(ai), AI_Player(ai)])
        game.play()
        deep_wins[str(game.opponent_index)] += 1
        # print("player %d wins after %d turns " % (game.opponent_index, game.nmove))

    # PvAI
    # scoring = lambda game: -100 if game.lose() else 0
    # ai = Negamax(13, scoring)
    # game = Hexapawn([Human_Player(), AI_Player(ai)])
    # game.play()
    # deep_wins[str(game.opponent_index)] += 1
    # print("player %d wins after %d turns " % (game.opponent_index, game.nmove))

    print("Shallow: ", shallow_wins)
    print("Deep: ", deep_wins)

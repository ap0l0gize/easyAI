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

    def __init__(self, players, size=(4, 4),probabilistic = False):
        self.probabilistic = probabilistic
        self.size = M, N = size
        p = [[(i, j) for j in range(N)] for i in [0, M - 1]]
        #[ [(0,1),(0,2),(0,3),(0,4)] , [(3,1),(3,2),(3,3),(3,4)]  ]
        for i, d, goal, pawns in [(0, 1, M - 1, p[0]), (1, -1, 0, p[1])]:
            players[i].direction = d
            players[i].goal_line = goal
            players[i].pawns = pawns #teraz to lista dictów

        self.players = players
      

    def valid_pawns(self,side)->list(tuple[int,int]):
        """ pass either self.opponent or self.player, this method returns a list of tuples of not captured pawns"""
        return [pos for pos in side.pawns if pos[0]!=-1 and pos[1]!=-1]
    
    def possible_moves(self):
        moves = []
        opponent_pawns = self.opponent.pawns
        d = self.player.direction
        for i, j in self.valid_pawns(self.player): #omit if there are captured pawns
            if (i + d, j) not in opponent_pawns:
                moves.append(((i, j), (i + d, j)))
            if (i + d, j + 1) in opponent_pawns:
                moves.append(((i, j), (i + d, j + 1)))
            if (i + d, j - 1) in opponent_pawns:
                moves.append(((i, j), (i + d, j - 1)))

        return list(map(to_string, [(i, j) for i, j in moves]))

    def opponent_possible_respawn(self) -> tuple[int, int] | None:
        captured = []
        for pos in self.opponent.pawns:
            if pos[0] == -1:
                captured.append((self.player.goal_line,pos[1]))
        if captured:
            return captured[random.randrange(0,len(captured))]
        return None
    def make_move(self, move):
        move = list(map(to_tuple, move.split(" ")))
        ind = self.player.pawns.index(move[0])
        self.player.pawns[ind] = move[1]

        if move[1] in self.opponent.pawns:
            # capturing pawns after move

            # if not hasattr(self.player, "captured_pawns"):
            #     self.player.captured_pawns = []
            # col = move[1][1]
            # start_row = self.opponent.goal_line
            # start_pos = (start_row, col)

            # self.player.captured_pawns.append(start_pos)
            # self.opponent.pawns.remove(move[1])

            idx = self.opponent.pawns.index(move[1])
            self.opponent.pawns[idx] = (-1,idx) #captured pawn is in -1 row at its starting column
                                       #captured pawn is opponents pawn than can now respawn again

        if self.probabilistic and random.random() < 0.1:     
            pos = self.opponent_possible_respawn()
                #pos[1] is essentially the index
            if pos:
                self.opponent.pawns[pos[1]]=(self.player.goal_line,pos[1])


    def lose(self):
        return any([i == self.opponent.goal_line for i, j in self.valid_pawns(self.opponent)]) or (
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
    from easyAI import AI_Player, Negamax

    # Keep scoring simple and terminal so the benchmark compares search depth only.
    scoring = lambda game: -100 if game.lose() else 0

    depth1 = 3
    depth2 = 6
    games_per_seat = 500
    base_seed = 1337

    def run_matchup(probabilistic: bool, seed_offset: int = 0) -> dict[str, int]:
        random.seed(base_seed + seed_offset)
        wins_by_depth = {str(depth1): 0, str(depth2): 0}
        mode_name = "probabilistic" if probabilistic else "deterministic"
        total_games = games_per_seat * 2

        def maybe_print_progress(done: int, last_printed: int) -> int:
            percent = int(done * 100 / total_games)
            if percent >= last_printed + 10 or done == total_games:
                print(f"[{mode_name}] progress: {percent}% ({done}/{total_games})")
                return percent
            return last_printed

        done = 0
        last_printed = -10

        for _ in range(games_per_seat):
            game = Hexapawn(
                [AI_Player(Negamax(depth1, scoring)), AI_Player(Negamax(depth2, scoring))],
                probabilistic=probabilistic,
            )
            game.current_player = 1
            game.play(verbose=False)
            winner_depth = depth1 if game.opponent_index == 1 else depth2
            wins_by_depth[str(winner_depth)] += 1
            done += 1
            last_printed = maybe_print_progress(done, last_printed)

        for _ in range(games_per_seat):
            game = Hexapawn(
                [AI_Player(Negamax(depth2, scoring)), AI_Player(Negamax(depth1, scoring))],
                probabilistic=probabilistic,
            )
            game.current_player = 1
            game.play(verbose=False)
            winner_depth = depth2 if game.opponent_index == 1 else depth1
            wins_by_depth[str(winner_depth)] += 1
            done += 1
            last_printed = maybe_print_progress(done, last_printed)

        return wins_by_depth

    deterministic = run_matchup(probabilistic=False, seed_offset=0)
    probabilistic = run_matchup(probabilistic=True, seed_offset=10_000)

    total_games = games_per_seat * 2
    print(f"Benchmark ({depth1} vs {depth2}, {total_games} games per mode)")
    print("Deterministic wins by depth:", deterministic)
    print("Probabilistic wins by depth:", probabilistic)

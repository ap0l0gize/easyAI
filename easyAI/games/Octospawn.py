from easyAI import TwoPlayerGame
import random
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
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
            players[i].random_column=None
            players[i].random_move_idxs = []
        self.players = players
        
      

    def valid_pawns(self, side) -> list[tuple[int, int]]:
        """ pass either self.opponent or self.player, this method returns a list of tuples of not captured pawns"""
        return [pos for pos in side.pawns if pos[0]!=-1 and pos[1]!=-1]
    
    def possible_moves(self, track_random_metadata: bool = True):
        moves = []
        random_move_idxs = []
        #this is for marking to the negamax that he is in a random node and is expected to use expecti
        opponent_pawns = self.opponent.pawns
        d = self.player.direction
        for i, j in self.valid_pawns(self.player): #omit if there are captured pawns
            is_random_pawn = (j == self.player.random_column)

            if (i + d, j) not in opponent_pawns:
                moves.append(((i, j), (i + d, j)))
                if is_random_pawn:
                    random_move_idxs.append(len(moves) - 1)
            if (i + d, j + 1) in opponent_pawns:
                moves.append(((i, j), (i + d, j + 1)))
                if is_random_pawn:
                    random_move_idxs.append(len(moves) - 1)
            if (i + d, j - 1) in opponent_pawns:
                moves.append(((i, j), (i + d, j - 1)))
                if is_random_pawn:
                    random_move_idxs.append(len(moves) - 1)
        if track_random_metadata:
            self.player.random_move_idxs = random_move_idxs
            self.player.random_column = None
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
                self.opponent.random_column = pos[1]  # Store just the column
                self.opponent.pawns[pos[1]]=(self.player.goal_line,pos[1])


    def lose(self):
        return any([i == self.opponent.goal_line for i, j in self.valid_pawns(self.opponent)]) or (
            self.possible_moves(track_random_metadata=False) == []
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
    import time
    from easyAI import AI_Player, Negamax

    # Keep scoring simple and terminal so the benchmark compares search depth only.
    scoring = lambda game: -100 if game.lose() else 0

    depth1 = 1
    depth2 = 3
    games_per_seat = 100
    base_seed = 1337
    total_games = games_per_seat * 2

    def run_matchup(
        probabilistic: bool,
        use_alpha_beta: bool = True,
        expecti: bool = False,
    ) -> tuple[dict[str, int], float]:
        random.seed(base_seed)
        wins_by_depth = {str(depth1): 0, str(depth2): 0}
        start = time.perf_counter()

        for _ in range(games_per_seat):
            game = Hexapawn(
                [
                    AI_Player(
                        Negamax(
                            depth1,
                            scoring,
                            use_alpha_beta=use_alpha_beta,
                           
                        )
                    ),
                    AI_Player(
                        Negamax(
                            depth2,
                            scoring,
                            use_alpha_beta=use_alpha_beta,
                            expecti_minimax=expecti,
                        )
                    ),
                ],
                probabilistic=probabilistic,
            )
            game.current_player = 1
            game.play(verbose=False)
            winner_depth = depth1 if game.opponent_index == 1 else depth2
            wins_by_depth[str(winner_depth)] += 1

        for _ in range(games_per_seat):
            game = Hexapawn(
                [
                    AI_Player(
                        Negamax(
                            depth2,
                            scoring,
                            use_alpha_beta=use_alpha_beta,
                           
                        )
                    ),
                    AI_Player(
                        Negamax(
                            depth1,
                            scoring,
                            use_alpha_beta=use_alpha_beta,
                            expecti_minimax=expecti,
                        )
                    ),
                ],
                probabilistic=probabilistic,
            )
            game.current_player = 1
            game.play(verbose=False)
            winner_depth = depth2 if game.opponent_index == 1 else depth1
            wins_by_depth[str(winner_depth)] += 1

        elapsed = time.perf_counter() - start
        return wins_by_depth, elapsed

    def plot_benchmark_results(results: list[dict]) -> None:
        """Generate benchmark visualization with win stats and runtime comparison."""
        if not HAS_MATPLOTLIB:
            print("matplotlib not available; skipping chart generation")
            return

        labels = [r["label"] for r in results]
        depth1_wins = [r["wins"][str(depth1)] for r in results]
        depth2_wins = [r["wins"][str(depth2)] for r in results]
        times = [r["time"] for r in results]

        fig, axes = plt.subplots(1, 2, figsize=(15, 6))

        x = range(len(labels))
        width = 0.35
        bars1 = axes[0].bar(
            [i - width / 2 for i in x],
            depth1_wins,
            width,
            label=f"Depth {depth1}",
            color="#2E86AB",
            alpha=0.8,
        )
        bars2 = axes[0].bar(
            [i + width / 2 for i in x],
            depth2_wins,
            width,
            label=f"Depth {depth2}",
            color="#A23B72",
            alpha=0.8,
        )

        axes[0].set_ylabel("Wins (symlog scale)", fontsize=12, fontweight="bold")
        axes[0].set_title("Negamax Performance: Wins by Depth", fontsize=13, fontweight="bold")
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(labels, rotation=45, ha="right")
        axes[0].legend(fontsize=11)
        # Use symlog so zero-win bars remain visible while small/large values separate better.
        axes[0].set_yscale("symlog", linthresh=1)
        axes[0].grid(axis="y", alpha=0.3, linestyle="--")
        axes[0].set_ylim(0, total_games * 1.05)

        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                axes[0].text(
                    bar.get_x() + bar.get_width() / 2,
                    height,
                    f"{int(height)}",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )

        bars3 = axes[1].bar(x, times, width=0.6, color="#F18F01", alpha=0.8)
        axes[1].set_ylabel("Runtime (seconds)", fontsize=12, fontweight="bold")
        axes[1].set_title("Benchmark Runtime Comparison", fontsize=13, fontweight="bold")
        axes[1].set_xticks(x)
        axes[1].set_xticklabels(labels, rotation=45, ha="right")
        axes[1].grid(axis="y", alpha=0.3, linestyle="--")

        for bar in bars3:
            height = bar.get_height()
            axes[1].text(
                bar.get_x() + bar.get_width() / 2,
                height,
                f"{height:.2f}s",
                ha="center",
                va="bottom",
                fontsize=9,
            )

        plt.tight_layout()
        output_file = "octospawn_benchmark.png"
        plt.savefig(output_file, dpi=150, bbox_inches="tight")
        print(f"\nSaved benchmark chart to: {output_file}")
        plt.show()

    def add_result(results: list[dict], label: str, wins: dict[str, int], elapsed: float) -> None:
        print(f"{label} wins by depth: {wins} (time: {elapsed:.2f}s)")
        results.append({"label": label, "wins": wins, "time": elapsed})

    print(f"Benchmark ({depth1} vs {depth2}, {total_games} games per mode)\n")

    benchmark_results = []

    print("=== Expecti Minimax ===")
    for use_alpha_beta in [True, False]:
        ab_label = " α-β" if use_alpha_beta else ""
        print(f"\nExpecti{ab_label}")

        wins, elapsed = run_matchup(
            probabilistic=False,
            use_alpha_beta=use_alpha_beta,
            expecti=True,
        )
        add_result(
            benchmark_results,
            f"Expecti det{' (α-β)' if use_alpha_beta else ''}",
            wins,
            elapsed,
        )

        wins, elapsed = run_matchup(
            probabilistic=True,
            use_alpha_beta=use_alpha_beta,
            expecti=True,
        )
        add_result(
            benchmark_results,
            f"Expecti prob{' (α-β)' if use_alpha_beta else ''}",
            wins,
            elapsed,
        )

    for use_alpha_beta in [True, False]:
        print(f"\n=== Negamax{' α-β' if use_alpha_beta else ''} ===")

        wins, elapsed = run_matchup(probabilistic=False, use_alpha_beta=use_alpha_beta)
        add_result(benchmark_results, f"Deterministic{' (α-β)' if use_alpha_beta else ''}", wins, elapsed)

        wins, elapsed = run_matchup(probabilistic=True, use_alpha_beta=use_alpha_beta)
        add_result(benchmark_results, f"Probabilistic{' (α-β)' if use_alpha_beta else ''}", wins, elapsed)

    plot_benchmark_results(benchmark_results)
        
    
from .engine import run_sample_battle


def main() -> None:
    state = run_sample_battle()
    print("\n".join(state.logs))


if __name__ == "__main__":
    main()

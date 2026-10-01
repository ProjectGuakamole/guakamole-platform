import time

WORKER_PLACEHOLDER_MESSAGE = (
    "Worker provisional de Guakamole iniciado. "
    "Sin gestión de colas todavía. Sujeto a cambios."
)


def main() -> None:
    print(WORKER_PLACEHOLDER_MESSAGE, flush=True)
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()

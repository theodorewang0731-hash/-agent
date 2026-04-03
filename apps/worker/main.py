import time


def run_demo_worker() -> None:
    print("RegentOS worker started")
    while True:
        # Placeholder loop for future queue consumers.
        time.sleep(5)


if __name__ == "__main__":
    run_demo_worker()

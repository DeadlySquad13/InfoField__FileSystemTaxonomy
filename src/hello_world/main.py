def hello_world(greeting: str, subject: str) -> str:
    return f"{greeting} {subject}!"


def main():
    print(hello_world("hello", "world"))


if __name__ == "__main__":
    main()

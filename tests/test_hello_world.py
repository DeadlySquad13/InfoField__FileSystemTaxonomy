import pytest

from hello_world.main import hello_world


def test_hello_world():
    assert hello_world("hello", "world") == "hello world!"
    assert hello_world("Hello", "world!") == "Hello world!!"
    assert hello_world("Privet", "mir") == "Privet mir!"


# The same as `test_hello_world` but more DRY.
@pytest.mark.parametrize(
    "greeting,subject,result",
    [
        ("hello", "world", "hello world!"),
        ("Hello", "world!", "Hello world!!"),
        ("Privet", "mir", "Privet mir!"),
    ],
)
def test_hello_world2(greeting: str, subject: str, result: str):
    assert hello_world(greeting, subject) == result

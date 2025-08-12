from app.utils import camel_to_snake


def test_camel_to_snake():
    print(camel_to_snake('userName'))
    print(camel_to_snake('apiKey'))
    print(camel_to_snake('user_id'))
    print(camel_to_snake('userName123'))


if __name__ == '__main__':
    test_camel_to_snake()



import hematite.raw.messages as m


def test_make_message():
    SomeMessage = m.make_message('SomeMessage', 'data')
    assert issubclass(SomeMessage, m.Message)

    instance = SomeMessage(10)
    assert isinstance(instance, m.Message)
    assert instance.type == 'somemessage'
    assert instance.data == 10

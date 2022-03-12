from resources.lib.storage import Storage
from tempfile import NamedTemporaryFile


def test_set_and_get():
    key = 1
    obj = {'test': 1, 'value': 123}

    with NamedTemporaryFile(suffix='.sqlite') as tmp:
        db = Storage(tmp.name)
        db.set(key, obj)
        obj2 = db.get(key)

    assert obj2 == obj


def test_get_missing():
    with NamedTemporaryFile(suffix='.sqlite') as tmp:
        db = Storage(tmp.name)

        res = db.get(1)

    assert res is None


def test_get_all():
    with NamedTemporaryFile(suffix='.sqlite') as tmp:
        db = Storage(tmp.name)

        db.set(1001, 1)
        db.set(1002, 2)
        db.set(1003, 3)

        res = db.get_all(reverse=False)
        res_reversed = db.get_all(reverse=True)

    assert res == [(1001, 1), (1002, 2), (1003, 3)]
    assert res_reversed == [(1003, 3), (1002, 2), (1001, 1)]


def test_get_all_update_order():
    with NamedTemporaryFile(suffix='.sqlite') as tmp:
        db = Storage(tmp.name)

        db.set(1001, 1)
        db.set(1002, 2)
        db.set(1003, 3)
        db.set(1001, -999)

        res = db.get_all()

    assert res == [(1002, 2), (1003, 3), (1001, -999)]


def test_replace():
    key = 1234

    with NamedTemporaryFile(suffix='.sqlite') as tmp:
        db = Storage(tmp.name)

        db.set(key, 'initial data')
        db.set(key, 'updated data')

        obj = db.get(key)
        all_objects = db.get_all()

    assert obj == 'updated data'
    assert len(all_objects) == 1


def test_delete():
    with NamedTemporaryFile(suffix='.sqlite') as tmp:
        db = Storage(tmp.name)

        db.set(1, {'data': 1})
        db.set(2, {'data': 2})
        db.set(3, {'data': 3})
        db.delete(2)

        res = [x[1] for x in db.get_all()]

    assert res == [{'data': 1}, {'data': 3}]


def test_delete_missing():
    with NamedTemporaryFile(suffix='.sqlite') as tmp:
        db = Storage(tmp.name)

        db.set(1, {'data': 1})
        db.set(2, {'data': 2})
        db.delete(999)

        res = [x[1] for x in db.get_all()]

    assert res == [{'data': 1}, {'data': 2}]


def test_reopen_database():
    with NamedTemporaryFile(suffix='.sqlite') as tmp:
        db = Storage(tmp.name)
        db.set(1, {'data': 123})
        del db

        db2 = Storage(tmp.name)
        res = [x[1] for x in db2.get_all()]

    assert res == [{'data': 123}]

from datetime import datetime

import pytest

from app import create_app
from app.extensions import db
from app.models import Client, ClientParking, Parking
from tests.factories import BaseFactory


@pytest.fixture(scope="function")
def app():
    test_app = create_app()
    test_app.config.update(
        {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SQLALCHEMY_TRACK_MODIFICATIONS": False}
    )

    with test_app.app_context():
        db.create_all()
        BaseFactory._meta.sqlalchemy_session = db.session

        test_client = Client(name="Ivan", surname="Ivanov", credit_card="4111111111111111", car_number="A111AA")
        test_parking = Parking(address="Test Street 1", opened=True, count_places=10, count_available_places=10)
        db.session.add_all([test_client, test_parking])
        db.session.commit()

        test_log = ClientParking(
            client_id=test_client.id, parking_id=test_parking.id, time_in=datetime.utcnow(), time_out=datetime.utcnow()
        )
        db.session.add(test_log)
        db.session.commit()

        yield test_app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_session(app):
    with app.app_context():
        yield db

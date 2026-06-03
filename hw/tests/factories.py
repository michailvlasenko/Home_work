import random

import factory
from faker import Faker

from app.extensions import db
from app.models import Client, Parking

fake = Faker()


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"


class ClientFactory(BaseFactory):
    class Meta:
        model = Client

    name = factory.Faker("first_name")
    surname = factory.Faker("last_name")
    car_number = factory.LazyFunction(lambda: fake.license_plate()[:10])
    credit_card = factory.LazyFunction(lambda: fake.credit_card_number() if random.random() > 0.5 else None)


class ParkingFactory(BaseFactory):
    class Meta:
        model = Parking

    address = factory.Faker("address")
    opened = factory.Faker("boolean")
    count_places = factory.Faker("random_int", min=10, max=100)
    count_available_places = factory.LazyAttribute(lambda o: o.count_places)

import pytest

# Измененные импорты
from models import Client, ClientParking, Parking
from tests.factories import ClientFactory, ParkingFactory


@pytest.mark.parametrize("url", ["/clients", "/clients/1"])
def test_get_methods_return_200(client, url):
    response = client.get(url)
    assert response.status_code == 200


def test_create_client(client, db_session):
    initial_count = db_session.query(Client).count()

    response = client.post(
        "/clients",
        json={"name": "Petr", "surname": "Petrov", "credit_card": "5555555555554444", "car_number": "B456DE"},
    )
    assert response.status_code == 201
    assert "id" in response.get_json()

    assert db_session.query(Client).count() == initial_count + 1


def test_create_parking(client, db_session):
    initial_count = db_session.query(Parking).count()

    response = client.post("/parkings", json={"address": "Nevsky 10", "count_places": 20, "count_available_places": 15})
    assert response.status_code == 201
    assert "id" in response.get_json()

    assert db_session.query(Parking).count() == initial_count + 1


@pytest.mark.parking
def test_park_car(client, db_session, test_client_id, test_parking_id):
    # Сначала проверяем, что клиент не активен на этой парковке
    existing_log = db_session.query(ClientParking).filter_by(
        client_id=test_client_id, parking_id=test_parking_id, time_out=None
    ).first()

    if existing_log:
        # Если есть активная запись, закрываем её
        existing_log.time_out = db_session.query(ClientParking).first().time_in
        db_session.commit()

    response = client.post("/client_parkings", json={"client_id": test_client_id, "parking_id": test_parking_id})
    assert response.status_code == 201

    parking = db_session.get(Parking, test_parking_id)
    assert parking.count_available_places == 9
    assert parking.opened is True

    log = db_session.query(ClientParking).filter_by(
        client_id=test_client_id, parking_id=test_parking_id, time_out=None
    ).first()
    assert log is not None and log.time_in is not None


@pytest.mark.parking
def test_leave_parking(client, db_session, test_client_id, test_parking_id):
    # Сначала создаем заезд
    client.post("/client_parkings", json={"client_id": test_client_id, "parking_id": test_parking_id})

    response = client.delete("/client_parkings", json={"client_id": test_client_id, "parking_id": test_parking_id})
    assert response.status_code == 200

    log = db_session.query(ClientParking).filter_by(
        client_id=test_client_id, parking_id=test_parking_id
    ).first()
    assert log.time_out is not None and log.time_out >= log.time_in

    parking = db_session.get(Parking, test_parking_id)
    assert parking.count_available_places == 10


@pytest.mark.parking
def test_leave_parking_no_card(client, db_session, test_parking_id):
    # Создаем клиента без карты
    response = client.post("/clients", json={"name": "NoCard", "surname": "User", "car_number": "X999ZZ"})
    client_id = response.get_json()["id"]

    # Создаем парковку
    parking_response = client.post("/parkings", json={"address": "Test Park", "count_places": 5, "count_available_places": 5})
    new_parking_id = parking_response.get_json()["id"]

    # Заезд
    client.post("/client_parkings", json={"client_id": client_id, "parking_id": new_parking_id})

    # Выезд без карты
    response = client.delete("/client_parkings", json={"client_id": client_id, "parking_id": new_parking_id})
    assert response.status_code == 400
    assert "No credit card attached" in response.get_json()["error"]


def test_create_client_with_factory(client, db_session):
    initial_count = db_session.query(Client).count()

    # Используем build() вместо create() чтобы не создавать в БД
    new_client = ClientFactory.build()

    response = client.post(
        "/clients",
        json={
            "name": new_client.name,
            "surname": new_client.surname,
            "credit_card": new_client.credit_card,
            "car_number": new_client.car_number,
        },
    )
    assert response.status_code == 201
    assert db_session.query(Client).count() == initial_count + 1
    assert "id" in response.get_json()


def test_create_parking_with_factory(client, db_session):
    initial_count = db_session.query(Parking).count()

    # Используем build() вместо create()
    new_parking = ParkingFactory.build()

    response = client.post(
        "/parkings",
        json={
            "address": new_parking.address,
            "count_places": new_parking.count_places,
            "count_available_places": new_parking.count_places,  # все места свободны
            "opened": new_parking.opened,
        },
    )
    assert response.status_code == 201
    assert db_session.query(Parking).count() == initial_count + 1
    assert "id" in response.get_json()
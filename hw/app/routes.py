from datetime import datetime

from flask import Blueprint, jsonify, request

from .extensions import db
from .models import Client, ClientParking, Parking

api = Blueprint("api", __name__)


@api.route("/clients", methods=["GET"])
def get_clients():
    clients = Client.query.all()
    return jsonify(
        [
            {"id": c.id, "name": c.name, "surname": c.surname, "credit_card": c.credit_card, "car_number": c.car_number}
            for c in clients
        ]
    )


@api.route("/clients/<int:client_id>", methods=["GET"])
def get_client(client_id):
    client = db.session.get(Client, client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404
    return jsonify(
        {
            "id": client.id,
            "name": client.name,
            "surname": client.surname,
            "credit_card": client.credit_card,
            "car_number": client.car_number,
        }
    )


@api.route("/clients", methods=["POST"])
def create_client():
    data = request.get_json()
    new_client = Client(
        name=data["name"],
        surname=data["surname"],
        credit_card=data.get("credit_card"),
        car_number=data.get("car_number"),
    )
    db.session.add(new_client)
    db.session.commit()
    return jsonify({"id": new_client.id}), 201


@api.route("/parkings", methods=["POST"])
def create_parking():
    data = request.get_json()
    available = data.get("count_available_places", data["count_places"])
    new_parking = Parking(
        address=data["address"],
        opened=data.get("opened", True),
        count_places=data["count_places"],
        count_available_places=available,
    )
    db.session.add(new_parking)
    db.session.commit()
    return jsonify({"id": new_parking.id}), 201


@api.route("/client_parkings", methods=["POST"])
def park_car():
    data = request.get_json()
    client_id = data.get("client_id")
    parking_id = data.get("parking_id")

    client = db.session.get(Client, client_id)
    parking = db.session.get(Parking, parking_id)

    if not client or not parking:
        return jsonify({"error": "Client or Parking not found"}), 404
    if not parking.opened:
        return jsonify({"error": "Parking is closed"}), 400
    if parking.count_available_places <= 0:
        return jsonify({"error": "No available places"}), 400

    parking.count_available_places -= 1
    log = ClientParking(client_id=client_id, parking_id=parking_id, time_in=datetime.utcnow())
    db.session.add(log)
    db.session.commit()
    return jsonify({"message": "Successfully parked", "log_id": log.id}), 201


@api.route("/client_parkings", methods=["DELETE"])
def leave_parking():
    data = request.get_json()
    client_id = data.get("client_id")
    parking_id = data.get("parking_id")

    log = ClientParking.query.filter_by(client_id=client_id, parking_id=parking_id, time_out=None).first()
    if not log:
        return jsonify({"error": "Active parking log not found"}), 404

    client = db.session.get(Client, client_id)
    if not client.credit_card:
        return jsonify({"error": "No credit card attached"}), 400

    parking = db.session.get(Parking, parking_id)
    parking.count_available_places += 1
    log.time_out = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": "Successfully left", "time_out": log.time_out.isoformat()}), 200

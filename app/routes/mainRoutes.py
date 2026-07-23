from flask import Blueprint

from app.controllers.mainController import landing_page


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def landing():
    return landing_page()

import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        from database import db
        from app import setup_app
        db.create_all()
        setup_app()
    with app.test_client() as client:
        yield client

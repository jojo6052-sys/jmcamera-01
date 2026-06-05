from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_imports_analytics.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
client = TestClient(app)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_import_products_csv_updates_analytics() -> None:
    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    try:
        csv_text = "\n".join(
            [
                "title,category,sale_price_jpy,final_profit_jpy,profit_margin,days_to_sell",
                "Canon EOS 5D,Camera,80000,20000,25,12",
                "Canon EOS 5D,Camera,90000,25000,27.5,8",
                "Nikon F3,Film Camera,70000,15000,21.4,20",
                ",Camera,10000,1000,10,5",
            ]
        )

        response = client.post(
            "/api/import/products",
            files={"file": ("products.csv", csv_text.encode("utf-8"), "text/csv")},
        )

        assert response.status_code == 200
        assert response.json() == {"imported_count": 3, "skipped_count": 1}

        best_sellers = client.get("/api/analytics/best-sellers")
        assert best_sellers.status_code == 200
        best_payload = best_sellers.json()
        assert best_payload[0]["title"] == "Canon EOS 5D"
        assert best_payload[0]["sales_count"] == 2
        assert best_payload[0]["total_profit_jpy"] == 45000.0

        categories = client.get("/api/analytics/categories")
        assert categories.status_code == 200
        category_payload = categories.json()
        assert category_payload[0]["category"] == "Camera"
        assert category_payload[0]["total_sales_jpy"] == 170000.0
    finally:
        if previous_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_override

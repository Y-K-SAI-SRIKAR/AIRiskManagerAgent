from app.database import Base, engine

from app.repositories.execution_model import Execution


def main():

    print("Creating Agent database tables...")

    Base.metadata.create_all(
        bind=engine
    )

    print("Database initialization complete.")


if __name__ == "__main__":
    main()
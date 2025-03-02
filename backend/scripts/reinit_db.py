import asyncio
from app.database_init import initialize_database
from app.database import create_tables

async def main():
    print("Reinitializing database...")
    create_tables()
    await initialize_database()
    print("Database reinitialization complete!")

if __name__ == "__main__":
    asyncio.run(main()) 
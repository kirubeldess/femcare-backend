from prisma import Prisma

db = Prisma()


async def connect_prisma():
    await db.connect()


async def disconnect_prisma():
    await db.disconnect()

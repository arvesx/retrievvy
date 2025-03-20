import asyncio
from retrievvy.nlp import embeddings

print("gamw to")


embeddings.start_worker()

async def main():
    encoded = await embeddings.get_async(["Sentence 1"*500, "Sentence 2", "Sentence 3"])
    for v in encoded:
        print(v)
        print(":))))")


asyncio.run(main())



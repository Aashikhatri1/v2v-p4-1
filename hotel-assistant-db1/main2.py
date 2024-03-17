import asyncio

import sys
sys.path.append('./components')
import speech_to_text1

async def main():
    transcript = await speech_to_text1.transcribe_stream()

    print(transcript)

    transcript_new = await speech_to_text1.transcribe_stream()
# Run the main async function
if __name__ == "__main__":
    asyncio.run(main())

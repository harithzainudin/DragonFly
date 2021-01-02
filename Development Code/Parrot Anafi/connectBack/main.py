from streamVideo import streamVideo
from streamingautomove import StreamingExample

def main():
    stream = streamVideo()
    stream.start()

    # stream = StreamingExample()
    # stream.start()
    stream.takeoff()
    stream.land()
    stream.land()
    stream.stop()

if __name__ == "__main__":
    main()
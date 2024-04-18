from vidgear.gears import CamGear
import cv2
import os
import sys
import math
import threading
from numpy import clip
from signal import signal, SIGWINCH, raise_signal
from typing import Callable
import argparse

parser = argparse.ArgumentParser(
    prog="Youtube Console",
    description="Watch Video From Youtube On Console"
)
parser.add_argument('--link')
import queue

#somewhere accessible to both:
callback_queue = queue.Queue()

def from_dummy_thread(func_to_call_from_main_thread):
    callback_queue.put(func_to_call_from_main_thread)

def from_main_thread_blocking():
    callback = callback_queue.get() #blocks until an item is available
    callback()

def from_main_thread_nonblocking():
    while True:
        try:
            callback = callback_queue.get(False) #doesn't block
        except queue.Empty: #raised when queue is empty
            break
        callback()

class Color:
    def __init__(self, r:int = 255, g:int = 255, b:int = 255) -> None:
        self._r = r
        self._g = g
        self._b = b

    @property
    def r(self):
        return self._r
    @property
    def g(self):
        return self._g
    @property
    def b(self):
        return self._b
    
    @r.setter
    def r(self, val):
        self._r = val
    @g.setter
    def g(self, val):
        self._g = val
    @b.setter
    def b(self, val):
        self._b = val
    
    def __str__(self) -> str:
        return "R: {} G: {} B: {}".format(self.r,self.g,self.b)
    def __add__(self,rhs):
        return Color(r=self.r + rhs.r, g=self.g + rhs.g, b=self.b + rhs.b)
    def __truediv__(self, div:int):
        return Color(round(self.r / div), round(self.g / div), round(self.b / div))
class ScreenSize:
    def __init__(self) -> None:
        self.width = 0
        self.height = 0

    def apply(self, t_size : os.terminal_size)->None:
        self.width = t_size.columns
        self.height = t_size.lines
    @property
    def width(self):
        return self._width
    @property
    def height(self):
        return self._height
    
    @width.setter
    def width(self, val):
        self._width = val
    @height.setter
    def height(self, val):
        self._height = val
    
    def __str__(self):
        return "Width: {} Height: {}".format(self.width,self.height)

class Screen:
    def __init__(self) -> None:
        self._size : ScreenSize = ScreenSize()

        signal(SIGWINCH, self.resize_handler)
        raise_signal(SIGWINCH)


    def draw_pixel(self, x:int,y:int,color:Color)->None:
        print("\033[{x};{y}H\033[38;2;{r};{g};{b}m#\033[0m"
                .format(x = x, y = y, r = color.r, g = color.g, b = color.b))

    def hide_cursor(self)->None: print("\e[?25l")
    def show_cursor(self)->None: print("\e[?25h")
    def clear(self)->None: 
        os.write(sys.stdout.fileno(),b"\033c")
        # if threading.current_thread().__class__.__name__ == '_MainThread':
        #     print("\033c", end="", flush=True)
        # else:
        #     from_dummy_thread(self.clear)
        #     from_main_thread_blocking
       
    def resize_handler(self,signum:int, frame)->None:
        self.size.apply(os.get_terminal_size())
        self.clear()

    @property
    def size(self):
        return self._size
    
class Stream:
    def __init__(self, url : str = "", receiver : Callable = None) -> None:
        self.handler = None
        self.receiver = receiver
        self.open(url=url)
    def bind(self, receiver : Callable = None) ->None:
        self.receiver = receiver

    def open(self, url:str):
        if len(url) > 0:
            self.handler = CamGear(
                source=url,
                stream_mode = True,
                logging = True
            )
    def start(self)->None:
        if self.handler is not None:
            self.handler.start()
            print(self.receiver)
            while True:
                if self.receiver is not None:
                    if not self.receiver(self.handler.read()):
                        break
                else:
                    if not self.index():
                        break
    
    def index(self)->bool:
        frame : cv2.Mat = self.handler.read()

        if frame is None:
            return False

        cv2.imshow("Live", frame)
        key = cv2.waitKey(5)
        if key == ord("q"):
            return False
        return True

class App:
    def __init__(self)->None:
        self.screen : Screen = Screen()
        self.stream : Stream= Stream(receiver=self.parser)
        self.stack : list = list()

    def parser(self, frame : cv2.Mat)->bool:
        if frame is not None:
            width, height, _ = frame.shape
            aspect_x = math.floor(width / self.screen.size.width)
            aspect_y = math.floor(height / self.screen.size.height)
            line : str = str()
           
            for y in range(0, self.screen.size.height):
                i = clip(y * aspect_y,0,height - 1)
                for x in range(0, self.screen.size.width):
                    j = clip(x * aspect_x, 0, width - 1)
                    color = Color(
                                r = frame[j][i][0],
                                g = frame[j][i][1],
                                b = frame[j][i][2]
                            )
                    line += "\033[38;2;{r};{g};{b}m{symbol}\033[0m".format(r = color.r, g = color.g, b = color.b,symbol=chr(9608))
                line += "\n"
            
            print(line, end="")
   
        if cv2.waitKey(5) == ord("q"):
            return False
        return True
    
    def execute(self):
        self.stream.start()
    

if __name__ == "__main__":
    args = parser.parse_args()
    app = App()
    app.stream.open(args.link)
    sys.exit(app.execute())


# stream = CamGear(source='https://www.youtube.com/watch?v=MyydQHomlQc', stream_mode = True, logging=True).start() # YouTube Video URL as input

# # # infinite loop
# # while True:
    
# #     frame : cv2.Mat = stream.read()
    
# #     # read frames

# #     # check if frame is None
# #     if frame is None:
# #         #if True break the infinite loop
# #         break
    
# #     # do something with frame here
    
# #     cv2.imshow("Output Frame", frame)
# #     # Show output window

# #     key = cv2.waitKey(1) & 0xFF
# #     # check for 'q' key-press
# #     if key == ord("q"):
# #         #if 'q' key-pressed break out
# #         break

# # cv2.destroyAllWindows()
# # # close output window

# # # safely close video stream.
# # stream.stop()




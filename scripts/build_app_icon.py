"""Render the repo-native scissors mark as a Windows shortcut icon."""
from pathlib import Path
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parents[1]
im=Image.new('RGBA',(256,256),(0,0,0,0));draw=ImageDraw.Draw(im)
draw.rounded_rectangle((0,0,255,255),radius=60,fill='#315fc5')
draw.ellipse((64,60,112,108),outline='white',width=17)
draw.ellipse((64,148,112,196),outline='white',width=17)
draw.line((108,100,184,176),fill='white',width=17)
draw.line((108,156,184,80),fill='white',width=17)
im.save(root/'desktop/public/autoclip.ico',sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])

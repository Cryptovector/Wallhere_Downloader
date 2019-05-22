import PIL
import pytesseract
import os

if os.name == 'nt':
	pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

def Solve_captcha(Img):
	width, height = Img.size 
	left = 0
	top = 0
	right = width*0.85
	bottom = height*0.75
	Img = Img.crop((left, top, right, bottom))
	pixels = Img.load()

	for i in range(Img.size[0]):
		for j in range(Img.size[1]):
			if not abs(pixels[i,j][0]-104)+abs(pixels[i,j][1]-102)+abs(pixels[i,j][2]-166) < 100:
				pixels[i,j] = (255,255,255)				

	return pytesseract.image_to_string(Img)

'''
Img = PIL.Image.open('D:\\Desktop\\NEWMEDIA\\Tools\\Python\\Developing\\Python_Wallhere\\captcha_5.png')
print(Solve_Capture(Img))
'''
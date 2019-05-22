import shutil
import requests
import os
import argparse
import json
import threading
import hashlib
import copy
import captcha_Solve
import PIL
import io
from lxml import html

threadcount = 0
Maxthread = 30
lock = threading.Lock()
Hashlock = threading.Lock()
threadready = threading.Event()
Redflag = False #False
Login = False #False
Cookies = None
Hashbase = {}

def get_Hash(byteseq):
	h = hashlib.sha256()
	h.update(byteseq)
	return h.digest()

def Wait_for_threads():
	while threadcount: #thread.join() is to slow 
		threadready.wait()
		threadready.clear()

def Solve_Captcha(url):
	Reqsession = requests.Session()

	if Login:
		Reqsession.cookies = Cookies

	for i in range(40):	
		Solution = ''
		Reloads = -1	
		while len(Solution) != 5: 
			Reloads += 1
			response = Reqsession.get('https://get.wallhere.com/captcha', headers={'referer': url})
			Img = PIL.Image.open(io.BytesIO(response.content))
			Solution = captcha_Solve.Solve_captcha(Img)

		payload = {'captcha': Solution}	
		response = Reqsession.post(url, data=payload)
		tree = html.fromstring(response.content)
		try:
			if not tree[0].text == 'Invalid captcha':
				print('Captcha solved after '+str(i+1)+' Trys and ' +str(Reloads)+ ' Reloads')
				return response.content
		except:
			print('Captcha solved after '+str(i+1)+' Trys and ' +str(Reloads)+ ' Reloads')
			return response.content		

def Login(Username, Password):
	global Cookies
	Wall_Session = requests.Session()

	payload = {'cmd': 'login', 'email': Username, 'password': Password}
	url = 'https://wallhere.com/de/login'
	response = Wall_Session.post(url, data=payload)
	Cookies = Wall_Session.cookies


def Download_Single_File(path, url):
	global Hashbase
	global Redflag
	global Cookies

	Reqsession = requests.Session()

	if Login:
		Reqsession.cookies = Cookies

	if not os.path.exists(path):
		response = Reqsession.get(url, stream=True)
		response_url = response.url
		if 'attachment&code' in response_url: 
			response_raw = Solve_Captcha(response_url)
		else:	
			response_raw = response.raw.read()
		response_rawt = copy.deepcopy(response_raw) #copy.deepcopy(response_raw)
		
		if Redflag:
			Imghash = get_Hash(response_rawt)
			#print(Imghash)
			Hashlock.acquire()
			if Imghash in Hashbase:
				print("Image already on Disk: [r] "+path)
				Hashlock.release()
				return
			else:
				Hashbase[Imghash] = None	
			Hashlock.release()
		
		with open(path, 'wb') as out_file:
			out_file.write(response_rawt)
		del response_rawt
		del response_raw

	else:
		print("Image already on Disk: "+path)		


def Site_Exists(url):
	request = requests.get(url)
	if request.status_code == 200:
		return 1
	else:	
		return 0

def Download_Image(path, url):
	global threadready
	global threadcount 
	global lock

	lock.acquire()
	threadcount += 1
	lock.release()

	Newpath = path+"\\"

	if not os.path.exists(path):
	   	os.makedirs(path)

	try:
	#for i in range(1):
		if Login:
			Wallurl = 'https://wallhere.com/de/wallpaper/' + url.split('/')[-1] 
			response_wall = requests.get(Wallurl)
			tree = html.fromstring(response_wall.content)
			for el in tree.iter('img'):
				try:
					if el.attrib['itemprop'] == 'contentURL':
						Wall_url = el.get('src')
				except:
					pass		

		else:
			Wall_url = url

		imgname = Wall_url.split("/")[-1]	
		finalpath = Newpath+"_"+imgname.split('.')[0]+'.'+imgname.split('.')[1].split('!')[0]
		print(finalpath)

		if Login:
			Download_Single_File(finalpath, url)
		else:	
			Download_Single_File(finalpath, url+'!d')

	except Exception as e:
		print(e)
		print("Image Donwload Failure")
		pass

	lock.acquire()
	threadcount -= 1
	lock.release()
	threadready.set() #Ready signal	


def Get_Site_url_list(url):

	Urllist = []
	Pagecount = 1
	if Site_Exists(url):
		while True:
			try:
				response = requests.get(url+"&page="+str(Pagecount)+"&format=json")# &page=83&format=json
				Urljson = json.loads(response.content)
				Urlhtml = Urljson['data']
				tree = html.fromstring(Urljson['data'])

				for i in tree.getchildren():
					try:
						if "h3" in str(i):
							return Urllist

						if Login:
							Requrl = 'https://wallhere.com/get/'+i[0].values()[0].split('/')[-1]
							Urllist.append(Requrl)
							print(Requrl)	
						else:	
							Imgurl = i[0][0].values()[2]
							Urllist.append(Imgurl[0:-2])
							print(Imgurl)

					except:
						pass	

				Pagecount += 1	
			except:
				break
	else:
		print("Site could not be Reached")

	return Urllist


def Download_all_Images(path , url):
	global threadready

	Urllist = reversed(Get_Site_url_list(url))

	for Urlentry in Urllist:
		print(Urlentry)

		if threadcount == Maxthread:
			threadready.wait()	

		Newthread = threading.Thread(target=Download_Image, args= (path, (Urlentry)))
		Newthread.start()
		threadready.clear()


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Wallhere Downloader')
	parser.add_argument('-i','--Image', action='store_false')
	parser.add_argument('-k','--Keyword', action='store_false')
	parser.add_argument('-r','--Red', action='store_false')
	parser.add_argument('-l','--Login', action='store_false')
	parser.add_argument('-u', '--Url',
		action="store", dest="Url",
		help="Url for Image or Keyword", default="")
	parser.add_argument('-d', '--destination',
		action="store", dest="destination",
		help="Path for Image files", default="")	
	parser.add_argument('-us', '--Username',
		action="store", dest="Username",
		help="Username for Auth", default="")	
	parser.add_argument('-pa', '--Password',
		action="store", dest="Password",
		help="Pass for Auth", default="")	
	parser.add_argument('-t', '--Threadnum',
		action="store", dest="Threadnum",
		help="Pass for Auth", default="")
	
	
	args = parser.parse_args()

	if not args.Red:
		Redflag = True

	if args.Threadnum != '':
		Maxthread = args.Threadnum

	if not args.Login:
		Maxthread = 1
		Login(args.Username, args.Password)
		Login = True
	else:
		Login = False			

	if (args.Image ^ args.Keyword):

		if not args.Keyword:
			Download_all_Images(args.destination, args.Url)
			Wait_for_threads()
		if not args.Image:
			Download_Image(args.destination, args.Url)
			Wait_for_threads()
	else:
		print("Usage: use -i or -k")	
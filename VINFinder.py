#
#  VINFinder.py
#  

import socket, threading, re, sys, csv, urllib, urlparse, httplib, time
from Queue import *
MAX_THREADS = 150
DEBUG = True
thread_pool = threading.BoundedSemaphore(value=MAX_THREADS)

def outputVIN(filename):
	while True:
		if allFoundVINs is None:
			return
		elif not allFoundVINs.empty():
			allFoundVINset.add(allFoundVINs.get())
			allFoundVINs.task_done()
		elif allFoundVINs.full():
			print "ALL FOUND VINS IS FULL!!"

def makeNewFinders():
	while True:
		if allVINFinders is None:
			return
		elif not allVINFinders.empty():
			thread_pool.acquire()
			finder = threading.Thread(target=VINFinderFunction, args=[allVINFinders.get()])
			finder.start()

def makeLinkRetrievers():
	while True:
		if allLRs is None:
			return
		elif not allLRs.empty():
			thread_pool.acquire()
			url = allLRs.get()
			retriever = threading.Thread(target=LinkRetrieverFunction, args=[url])
			retriever.start()

def readMessageFromServer(host, url):
	#Open the connection and get the response.
	try:
		conn = httplib.HTTPConnection(host, timeout=10)
		truncated_url = urlparse.urlparse(url)
		conn.request("GET",truncated_url.path + "?" + truncated_url.query)
		res = conn.getresponse()
		if res.status == 302:
			new_location_url = res.getheader("Location")
			redirected_url = urlparse.urlparse(new_location_url)
			return readMessageFromServer(redirected_url.netloc,new_location_url)
		return res.read()
	except:
		print "Unexpected error:", sys.exc_info()[0]
		return ""
		
def LinkRetrieverFunction(url):
	#Connect to the eBay page.
	recv_message = readMessageFromServer(urlparse.urlparse(url).hostname,url)
	#Look for all the car links on the search page.
	re_matches = re.findall('a href="(http://cgi.ebay.com/.*?)"', recv_message)
	for re_match in re_matches:
		allVINFinders.put(re_match)
	thread_pool.release()
	allLRs.task_done()

def VINFinderFunction(url):
	parsed_url = urlparse.urlparse(url)
	recv_message = readMessageFromServer(parsed_url.hostname, parsed_url.path)
	dataMatch = re.search("VIN#.*?<span>(\w+)</span>",recv_message)
	if dataMatch is not None:
		allFoundVINs.put(dataMatch.group(1))
	thread_pool.release()
	allVINFinders.task_done()
	if DEBUG: print "VINs left to retrieve ["+repr(allVINFinders.qsize())+"]"
		
#Create a queue of all the VINs we find that we need to print.
allFoundVINs = Queue()
allFoundVINset = set()
allLRs = Queue()
allVINFinders = Queue()
filename = 'VINs.csv'
output = open(filename,'wb+')
VINWriter = threading.Thread(target=outputVIN, args=[filename])
VINWriter.daemon = True
VINWriter.start()

VINFinderMaker = threading.Thread(target=makeNewFinders)
VINFinderMaker.daemon = True
VINFinderMaker.start()

LinkRetrieverMaker = threading.Thread(target=makeLinkRetrievers)
LinkRetrieverMaker.daemon = True
LinkRetrieverMaker.start()

url = 'http://www.ebay.com/sch/Cars-Trucks-/6001/i.html'
#Check how many pages can be searched.
print "Connecting to first page..."
recv_message = readMessageFromServer(urlparse.urlparse(url).hostname,url)
matches = re.search("<span class=\"page\">Page\s*(\d+)\s*of\s*(\d+)</span>",recv_message)
number_of_pages = 286#int(matches.group(2))

#Look for the VINs on all the pages.
print "Looking for VINs on ["+ repr(number_of_pages) +"] pages."
for page_num in range(1,number_of_pages):
	allLRs.put(url+"?_pgn="+repr(page_num))
	
#Wait for all tasks to be done.
allLRs.join()
allVINFinders.join()
print "Finished finding all VINs."
allFoundVINs.join()
print "Found ["+repr(len(allFoundVINset))+"] VINs."
for VIN in allFoundVINset:
	output.write(VIN+'\n')

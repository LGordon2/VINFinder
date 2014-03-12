#!/usr/bin/python

#
#  VINFinder.py
#  

from pyquery import PyQuery as pq
from lxml import etree
import socket, threading, re, sys, csv, urllib, urlparse, httplib, time

from Queue import *
MAX_THREADS = 25
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
			if DEBUG: print "VINs left to retrieve ["+repr(allVINFinders.qsize()+1)+"]"
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
	pyqueryObj = pq(url)
	dataMatch = ""
	for element in pyqueryObj("td.attrLabels"):
	  if element.text_content().strip() == "VIN (Vehicle Identification Number):" or element.text_content().strip() == "Hull ID Number:":
	    dataMatch = element.getnext().text_content().strip()
	    break
	if dataMatch != "":
		allFoundVINs.put(dataMatch)
	thread_pool.release()
	allVINFinders.task_done()
	
		
#Create a queue of all the VINs we find that we need to print.
allFoundVINs = Queue()
allFoundVINset = set()
allLRs = Queue()
allVINFinders = Queue()
filename = 'VINs_'+repr(int(time.time()))+'.csv'
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

if len(sys.argv) > 1:
	if sys.argv[1] == 'boat':
		url = 'http://www.ebay.com/sch/Boats-/26429/i.html?_ipg=200'
	elif sys.argv[1] == 'boat':
		url = 'http://www.ebay.com/sch/Cars-Trucks-/6001/i.html?_ipg=200'
	elif sys.argv[1] == 'url':
		if len(sys.argv) == 2:
			print "Not enough arguments specified for this option."
			exit(1)
		url = sys.argv[2]
	else:
		url = 'http://www.ebay.com/sch/Cars-Trucks-/6001/i.html?_ipg=200'
else:
	url = 'http://www.ebay.com/sch/Cars-Trucks-/6001/i.html?_ipg=200'

#Fix for when we are looking on multiple pages
if "?" not in url:
	url += "?"

#Check how many pages can be searched.
print "Connecting to first page..."
d = pq(url=url)
number_of_pages = int(d("span.rcnt").text().replace(",",""))/200 + 1

#Look for the VINs on all the pages.
print "Looking for VINs on ["+ repr(number_of_pages) +"] pages."

if number_of_pages == 1:
	page_range = [1] 
else:
	page_range = range(1,number_of_pages)

for page_num in page_range:
	allLRs.put(url+"&_pgn="+repr(page_num))
	
#Wait for all tasks to be done.
allLRs.join()
allVINFinders.join()
print "Finished finding all VINs."
allFoundVINs.join()
print "Found ["+repr(len(allFoundVINset))+"] VINs."
for VIN in allFoundVINset:
	output.write(VIN+'\n')

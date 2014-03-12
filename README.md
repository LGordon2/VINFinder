VINFinder
=========
Author: Lew Gordon

Finds VINs using eBay.

###Requirements:

- [Python 2.7.x](http://www.python.org/download/releases/2.7/) (developed on Python 2.7.5)
- [Pip](http://pip.readthedocs.org/en/latest/installing.html)
- [PyQuery](https://pypi.python.org/pypi/pyquery) (if you are having issues with Pip..)

###Getting started:

    pip install -r requirements.txt (Optional if you manually installed pyquery)
    python VINFinder.py

###Example with custom url:

    python VINFinder.py url http://www.ebay.com/sch/Cars-Trucks-/6001/i.html?_ipg=200

###Notes:

* The "boat" argument creates a predefined search on boats.
* If you use the "url" argument the next argument can be a custom url to scrape from.
* The file VINs_TIMESTAMP.csv will be created when the script is run.

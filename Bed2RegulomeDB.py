import urllib, urllib2, time


# HttpBot
# -------
# This class opens a handler and can GET and POST to a url.
#
class HttpBot:
    """an HttpBot represents one browser session, with cookies."""
    def __init__(self):
        cookie_handler= urllib2.HTTPCookieProcessor()
        redirect_handler= urllib2.HTTPRedirectHandler()
        http_handler= urllib2.HTTPHandler()
        error_handler=urllib2.HTTPErrorProcessor()
        self._opener = urllib2.build_opener(cookie_handler,redirect_handler, http_handler,error_handler)
        #urllib2.install_opener(self._opener)

    def GET(self, url):
        return self._opener.open(url).read()

    def POST(self, url, parameters):     
        user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        headers = { 'User-Agent' : user_agent }
        return self._opener.open(url, urllib.urlencode(parameters))
    

def RegDBparser(file):
    import csv
    myfile = csv.reader(open(file, 'rb'),  delimiter = '\t')
    coordslist = list()
    for row in myfile:
    	coordslist.append(row[0]+':'+row[1]+'-'+row[2])
    return(coordslist)



# getRegulomeDBData
# -----------------
# This function takes a string of 'chr_:pos-pos\nchr_:pos-pos...' and returns a string with
# regulatory information for each site.
#

def getRegulomeDBDataWithText(coordText):
    #print "next"
    if coordText == "": return ""
    bot = HttpBot()
    trials=0
    while trials<100:
        try:
            x = bot.POST('http://regulome.stanford.edu/results', {'data': coordText})
            pageData = x.read();
            pageData = pageData.split("<input type=\"hidden\" name=\"sid\" value=\"")
            sid = pageData[1].split("\" />")[0]
            x = bot.POST("http://regulome.stanford.edu/download", {'format':'full', 'sid':sid})
            pageData = x.read()
            pageData = pageData.split("\n", 1)
            pageData = pageData[1]
            return pageData
        except:
            print "error! trial", trials
            time.sleep(0.25)
        trials+=1
    print "error can't be fixed by trying again..."
    return ""


def getRegulomeDBDataWithList(file, outfile, numPerRequest):
    coordList = RegDBparser(file)
    outfile = open(outfile,  'w')
    sitesToAnnotate=coordList
    counter = 0
    while True:
        currentSubset=""
        total=len(coordList)
        unannotatedSites=[]
        sofar=0
        while sofar<total:
            i=0
            while i<numPerRequest:
                if sofar>=total: break
                if "MT" not in coordList[sofar]:
                    currentSubset+="\n"+coordList[sofar]
                sofar+=1
                i+=1
            print str(sofar)+'/'+str(total)
            currentAnnotations = getRegulomeDBDataWithText(currentSubset)
            unannotatedSites += getUnannotatedSites(currentSubset, currentAnnotations)
            outfile.write(getRegulomeDBDataWithText(currentSubset)+"\n")
            currentSubset=""
        counter+=1
        sitesToAnnotate=unannotatedSites
        if len(sitesToAnnotate)==0: break
        if counter > 1: 
            print "sites won't annotate..."
            print sitesToAnnotate
            break


def getUnannotatedSites(input, output): 
    inputSites={}
    inputLines=input.split("\n")
    for line in inputLines:
        vals = line.split("\t")
        if len(vals)>1:
            site = vals[0]+"\t"+vals[1]
            inputSites[site]=""
    badSites=[]
    outputLines=output.split("\t")
    for line in outputLines:
        vals = line.split("\t")
        if len(vals)>1:
            site = vals[0].strip("chr")+"\t"+vals[1]
            if site not in inputSites:
                badSites.append(site)
        
    return badSites


if __name__ == '__main__':
    import sys
    from optparse import OptionParser, OptionGroup  
    usage = "usage: %prog -i <input file> -o <output file> -n <numPerRequest>"
    
    parser = OptionParser(usage = usage)
    parser.set_defaults(infilename="None")
    parser.add_option("-i", "--input", dest="infilename",help="Input bed file", metavar="FILE")

    parser.set_defaults(outfilename="None")
    parser.add_option("-o", "--output", dest="outfilename",help="Ouput RegulomeDB file results", metavar="FILE")

    parser.set_defaults(numPerRequest=10)
    parser.add_option("-n", "--numPerRequest", dest="numPerRequest",help="Number of query per request [default: %default]", metavar="STR")
    
    (options, args) = parser.parse_args()

    if (sys.argv[1:] == []):
        parser.print_help()
    else:
    	file=options.infilename        
    	outfile=options.outfilename
    	numPerRequest=options.numPerRequest
    	getRegulomeDBDataWithList(file, outfile, numPerRequest)

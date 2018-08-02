import face_recognition, os
import json
import urllib.request
import pickle
import numpy as np
import argparse
from imutils import paths
import cv2
from string import Template


def loadBioguide():
    
    print("[INFO] loading bioguide...")

    bioguide = []
    
    dataurls = ['https://theunitedstates.io/congress-legislators/legislators-historical.json', 'https://theunitedstates.io/congress-legislators/legislators-current.json']
    #dataurls = ['https://theunitedstates.io/congress-legislators/legislators-current.json']
    
    for(i, dataurl) in enumerate(dataurls):
        with urllib.request.urlopen(dataurl) as url:
            bioguide.extend(json.loads(url.read().decode()))
    
            #data = json.loads(url.read().decode())
    return bioguide
    

def getNameFromBioguide(key):
    
    key_index = next((idx for (idx, d) in enumerate(bioguideDict) if d["id"]["bioguide"] == key), -1)
    
    name = "Not Found"
       
    if (key_index != -1):
        try:
            name = bioguideDict[key_index]["name"]["official_full"]
        except KeyError:
            fname = bioguideDict[key_index]["name"]["first"]
            lname = bioguideDict[key_index]["name"]["last"]
            name = "{} {}".format(fname, lname)
        
    return name


def getTermFromBioguide(key):
    key_index = next((idx for (idx,d) in enumerate(bioguideDict) if d["id"]["bioguide"] == key), -1)
    
    firstTermStart = "Not Found"
    
    if (key_index != -1):
        try:
            firstTermStart = bioguideDict[key_index]["terms"][0]["start"]
        except Exception as e:
            firstTermStart = "unknown"
            
    return firstTermStart

def makeEncodings(bioguideDict):
        
    pickleData = []
    for(i, bioguide) in enumerate(bioguideDict):
        bid = bioguideDict[i]['id']['bioguide']
        print("[INFO] processing image {}/{} {}".format(i+1, len(bioguideDict), bid))
        addEncodingFor(bid, pickleData)
        
    print("[INFO] serializing encodings...")
    fd = open(args['pickle'],"wb")
    fd.write(pickle.dumps(pickleData))
    fd.close()
    print("[INFO] encodings saved to {}".format(args['pickle']))

def addEncodingFor(bgid, data):
    
    # get the photo if possible
    # photos from https://github.com/unitedstates/images

    url = "https://theunitedstates.io/images/congress/225x275/{}.jpg".format(bgid)
    tmpfile = "/tmp/{}.jpg".format(bgid)
      
    name = getNameFromBioguide(bgid)
 
    try:
        urllib.request.urlretrieve(url, tmpfile)
    except Exception as e:
        print("[WARN] There was a problem fetching image for {} ({}) : {}".format(name, getTermFromBioguide(bgid), bgid))
        return
        
    image = cv2.imread(tmpfile)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
    # get the bounding box
    boxes = face_recognition.face_locations(rgb, model=args["detection_method"])
    if(len(boxes) == 0):
        print("[WARN] No face found for{} : {}".format(name, url))
        return
        
    # compute face encoding
    encodings = face_recognition.face_encodings(rgb, boxes)
        
    d = [{"url":url, "encoding":enc, "name":name, "bioguideid": bgid}
        for (box, enc) in zip(boxes, encodings)]
            
    data.extend(d)
        
    
def writeImageWithURL(fd, url, name, cssClass):
    # add the photo
    fd.write("\t<div class=\"image {}\">\r\n".format(cssClass))
    fd.write("\t\t<img src='{imgurl}'>\r\n".format(imgurl=url))
    # add a caption
    fd.write("\t\t<div class=\"caption\">{}</div>\r\n".format(name))
    fd.write("\t</div>\r\n")
    
           
def makePage(tolerances, outputFile='index.html'):  
    print("[INFO] loading encodings...")
            
    pickleData = pickle.loads(open(args['pickle'], "rb").read())
    data = np.array(pickleData)
    encodings = [d["encoding"] for d in data]
    urls = [d["url"] for d in data]
    names = [d["name"] for d in data]
    bioguideIDs = [d["bioguideid"] for d in data]
    
    print("[INFO] writing page...")
    
    # start writing the outputFile page
    fd = open(outputFile, "w+")
    fhead = open("header.html","r")
    fd.write(fhead.read())
    fd.flush()
    fhead.close()
    
    possibleMatches = (len(urls) * (len(urls)-1))/2
    fd.write("{} Faces -- with a possible {} incorrect matches n(n-1)/2<p>".format(len(urls), int(possibleMatches)))
    
    # create the tab bar
    fd.write("<div class='tab'>")
    
     # add an 'All' tab   
    fd.write("<button class=\"tablinks\" onclick=\"openTab(event, 'all')\">All</button>\r\n")
    
    # create a tab for each tolerance that will be used
    for tolerance in tolerances:
        tabname = "tab{}".format(tolerance)
        fd.write("<button class=\"tablinks\" onclick=\"openTab(event, '{tabname}')\">T{tol}</button>\r\n".format(tabname=tabname, tol=tolerance))
    
    fd.write("</div>\r\n");
    
    # the 'All' tab content
    tabname="all"
    fd.write("<div id=\"{tabname}\" class=\"tabcontent\">\r\n".format(tabname=tabname))
    fd.write("<div class=\"row\">\r\n")

    for (i, url) in enumerate(urls):
        writeImageWithURL(fd, url, names[i], "subject")
        
    fd.write("</div></div>\r\n") # close the row
    
    # now the tolerance tabs   
    matchInfoDict = {}
    
    # write each of the tabs
    for (tindex, tolerance) in enumerate(tolerances):
        print("[INFO] writing tolerance tab for {}".format(tolerance))

        tkey = "MATCHES{}".format(tindex)
        tper = "MPER{}".format(tindex)
        
        tabname="tab{}".format(tolerance)
        fd.write("<div id=\"{tabname}\" class=\"tabcontent\">\r\n".format(tabname=tabname))
        fd.write("Tolerance: {} Matches: ${}  Error: ${} <p>".format(tolerance, tkey, tper))
        
        matchInfoDict[tkey] = 0
        
        # for each politician, how many others look similar within tolerance?
        for (index, known_face) in enumerate(encodings):
                
            # results is an array of True/False telling if the known face matched anyone in the encodings array
            results = face_recognition.compare_faces(encodings, known_face, tolerance=tolerance)
            # reduce results to an array of indicies where the results is True
            matches = [i for i, x in enumerate(results) if x]
    
            if len(matches) > 1: # match self and at least one other 
                        
                # add this CP's look-alikes
                fd.write("<div class=\"row\">\r\n")
                
                writeImageWithURL(fd, urls[index], names[index], "subject")
                
                # spacer
                fd.write("\t<div class=\"spacer\">&nbsp;&rarr;&nbsp;</div>\r\n")
                
                for (i, match) in enumerate(matches):
                    if(urls[match] != urls[index]): # don't write a self-match
                        matchInfoDict[tkey] = matchInfoDict[tkey]+1
                        writeImageWithURL(fd, urls[match], names[match], "match")
    
                fd.write("</div>\r\n") # close the row
        
        fd.write("</div>\r\n") # close tabcontent
        
        matchInfoDict[tkey] = int(matchInfoDict[tkey]/2)
        matchInfoDict[tper] = "{0:.5f}%".format(matchInfoDict[tkey]/possibleMatches * 100)

    # add the html footer
    ffoot = open("footer.html","r")
    fd.write(ffoot.read())
    fd.flush()
    ffoot.close()    
    fd.close()
    
    # now swap in the final numbers and percents
    fd = open(outputFile)
    src = Template(fd.read())
    fd.close()

    fd = open(outputFile,"w+")
    fd.write(src.substitute(matchInfoDict))
    fd.close()

tolerances=[0.6,0.55, 0.5, 0.45,0.44,0.43, 0.429, 0.428, 0.427, 0.426, 0.425]
#tolerances=[0.6, 0.55]

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--dataset", type=str, help="path to input directory of faces/images")
ap.add_argument("-e", "--encode", type=bool, default=False, help="True to encode faces")
ap.add_argument("-d", "--detection-method", type=str, default="hog", 
    help="face detection model to use: either `hog` or `cnn`")
ap.add_argument("-p", "--pickle", type=str, default="ecodings.pickle", help="name of pickle file")	
ap.add_argument("-o", "--output", type=str, default="index.html", help="name of output html file")	
args = vars(ap.parse_args())

bioguideDict = loadBioguide()

if (args["encode"]):
    makeEncodings(bioguideDict)
    
makePage(tolerances, args['output'])

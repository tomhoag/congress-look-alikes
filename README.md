# Congress Look Alikes

So how much does congress look like itself?  

Using the resources found @ https://github.com/unitedstates/images & https://theunitedstates.io/  and making use of [opencv](https://github.com/opencv/opencv), [dlib](https://github.com/davisking/dlib) and [face_recognition](https://github.com/ageitgey/face_recognition#face-recognition) and a few other libs, some code from [Adrian](https://www.pyimagesearch.com) and [Adam](https://medium.com/@ageitgey), I cobbled together this little project.

The results might still be available:

[Current and past members of congress](http://congress-look-alikes.s3-website-us-east-1.amazonaws.com/all.html)

[Current members of congress](http://congress-look-alikes.s3-website-us-east-1.amazonaws.com/current.html)

## Methodology

Using the roster of all current and past congress people (https://theunitedstates.io), any congress person that has a image available is encoded and saved with some other meta info in the pickle file.

Using the encoded faces, each image is then compared to all of the other images.  The comparison is run multiple times, tweaking the tolerance value used with face_recognition.   If an image matches at least one other image (other than itself), the match(es) are displayed on the output page.

While the initial pretext of this exercise is to discern the similarity among congress people's images, it quickly becomes an exercise in overfitting the solution to the data.


## Run the code
You can run the code yourself too -- you will need to install the dependencies into your python environment -- sorry no requirements file at the moment.

face_recognition, os, json, urllib.request,pickle, numpy, argparse, imutils, cv2, string 

python match.py -h will then help you get started


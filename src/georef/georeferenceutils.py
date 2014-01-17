'''
Created on Oct 15, 2013

@author: mendt
'''
import subprocess

""" function: parseYSize

    @param - imageFile {String} - path to a image file
    @return - {Integer} - value which represents the y size of the file
    
    This function parse the x,y size of a given image file """
def parseXYSize(imageFile):
    # run gdalinfo command on imageFile and catch the response via Popen
    response = subprocess.Popen("gdalinfo %s"%imageFile, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    
    # read the console output line by line
    for line in response.stdout:
        if 'Size is ' in line:
            x,y = line[8:].split(', ')
            #print "X: %s, Y: %s"%(x,y)
            return float(x),float(y)

""" Functions for getting the gcps. """
def getGCPsAsString(unorderedPixels, verzeichnispfad, georefCoords):
    pure_gcps = getGCPs(unorderedPixels, verzeichnispfad, georefCoords)
    str_gcps = []
    for tuple in pure_gcps:
        string = " ".join(str(i) for i in tuple[0])+", "+" ".join(str(i) for i in tuple[1])
        str_gcps.append(string)
    return str_gcps

def getGCPs(unorderedPixels, verzeichnispfad, georefCoords):
        # transformed the pixel coordinates to the georef coordinates by recalculating the y values, 
        # because of a different coordinate origin
        transformedUnorderedPixels = []
        xSize, ySize = parseXYSize(verzeichnispfad)
        for tuple in unorderedPixels:
            transformedUnorderedPixels.append((tuple[0],ySize-tuple[1]))

        # now order the pixel coords so that there sorting represents the order llc, ulc, urc, lrc
        transformedOrderedPixels = orderPixels(transformedUnorderedPixels)

        # now create the gcp list
        try:
            gcpPoints = []
            for i in range(0,len(transformedOrderedPixels)):
                pixelPoints = (transformedOrderedPixels[i][0],transformedOrderedPixels[i][1])
                georefPoints = (georefCoords[i][0],georefCoords[i][1])
                gcpPoints.append((pixelPoints,georefPoints))
            return gcpPoints
        except:
            raise  
               
def orderPixels(unorderdPixels):
    """
    Function brings a list of tuples which are representing the clipping parameter from the client 
    in the order llc ulc urc lrc and gives them back at a list. Only valide for pixel coords
        
    @param clippingParameterList: list whichcomprises 4 tuples of x,y coordinates
    """
    xList = []
    yList = []
    for tuple in unorderdPixels:
        xList.append(tuple[0])
        yList.append(tuple[1])
             
    orderedList = [0, 0, 0, 0] 
    xList.sort() 
    yList.sort()
    for tuple in unorderdPixels:
        if (tuple[0] == xList[0] or tuple[0] == xList[1]) and \
            (tuple[1] == yList[2] or tuple[1] == yList[3]):
            orderedList[0] = tuple
        elif (tuple[0] == xList[0] or tuple[0] == xList[1]) and \
            (tuple[1] == yList[0] or tuple[1] == yList[1]):
            orderedList[1] = tuple 
        elif (tuple[0] == xList[2] or tuple[0] == xList[3]) and \
            (tuple[1] == yList[0] or tuple[1] == yList[1]):
            orderedList[2] = tuple 
        elif (tuple[0] == xList[2] or tuple[0] == xList[3]) and \
            (tuple[1] == yList[2] or tuple[1] == yList[3]):
            orderedList[3] = tuple 
    return orderedList 

""" Functions for creating the commands for command line """

""" function: addGCPToTiff

    @param - gcPoints {list of gcp} - list of ground control points
    @param - srid {Integer} - epsg code of coordiante system
    @param - srcPath {String}
    @param - destPath {String}
    @return - command {String}
    
    Add the ground control points via gdal_translate to the src tiff file """
def addGCPToTiff(gcPoints,srs,srcPath,destPath):
            
    def addGCPToCommandStr(command,gcPoints):
        for string in gcPoints:
            command = command+"-gcp "+str(string)+" "
        return command
        
    command = "gdal_translate --config GDAL_CACHEMAX 500 -a_srs epsg:%s "%srs
    command = addGCPToCommandStr(command,gcPoints)
    command = command+str(srcPath)+" "+str(destPath)
    return command

""" function: georeferenceTiff_fast

    @param - shapefilePath {String}
    @param - srid {Integer} - epsg code of coordiante system
    @param - srcPath {String}
    @param - destPath {String}
    @return - command {String}
    
    Georeferencing via gdalwarp """
def georeferenceTiff_fast(shapefilePath, srid, srcPath, destPath):
    command = "gdalwarp --config GDAL_CACHEMAX 500 -wm 500 -overwrite -co TILED=YES -cutline %s \
             -crop_to_cutline -t_srs epsg:%s %s %s"%(shapefilePath,srid,srcPath,destPath)
    return command

""" function: georeferenceTiff_stable

    @param - shapefilePath {String}
    @param - srid {Integer} - epsg code of coordiante system
    @param - srcPath {String}
    @param - destPath {String}
    @return - command {String}
    
    Georeferencing via gdalwarp """
def georeferenceTiff_stable(shapefilePath, srid, srcPath, destPath):
    command = "gdalwarp --config GDAL_CACHEMAX 500 -wm 500 -overwrite -co TILED=YES -co COMPRESS=JPEG \
            -co JPEG_QUALITY=75 -co PHOTOMETRIC=RGB -co ALPHA=NO -co INTERLEAVE=BAND -cutline %s \
            -crop_to_cutline -t_srs epsg:%s %s %s"%(shapefilePath,srid,srcPath,destPath)
    return command

def addOverviews(targetPath, overviewLevels):
    command = "gdaladdo --config GDAL_CACHEMAX 500 -r average %s %s"%(targetPath,overviewLevels)
    return command 
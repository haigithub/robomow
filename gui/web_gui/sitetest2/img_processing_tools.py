#!/usr/bin/env python

from PIL import Image
import numpy as np
from PIL import ImageStat
import mahotas
import numpy as np

def image2array(img):
	"""given an image, returns an array. i.e. create array of image using numpy """
	return np.asarray(img)

###########################################################

def array2image(arry):
	"""given an array, returns an image. i.e. create image using numpy array """
	#Create image from array
	return Image.fromarray(arry)

###########################################################

def PILtoCV(PIL_img):
	cv_img = cv.CreateImageHeader(PIL_img.size, cv.IPL_DEPTH_8U, 1)
	cv.SetData(cv_img, PIL_img.tostring())
	return cv_img

###########################################################

def CVtoPIL(img):
	"""converts CV image to PIL image"""
	cv_img = cv.CreateMatHeader(cv.GetSize(img)[1], cv.GetSize(img)[0], cv.CV_8UC1)
	#cv.SetData(cv_img, pil_img.tostring())
	pil_img = Image.fromstring("L", cv.GetSize(img), img.tostring())
	return pil_img
###########################################################

def CalcHistogram(img):
	#calc histogram of green band
	bins = np.arange(0,256)
	hist1 = image2array(img)
	H, xedges = np.histogram(np.ravel(hist1), bins=bins, normed=False)
	return H	

def WriteMeterics(image, classID, data_filename):
	
	if len(image.getbands()) == 3:
		#write class data to file
		f_handle = open(data_filename, 'a')
		f_handle.write(str(classID))
		f_handle.write(', ')
		f_handle.close()
		#calculate LBP histogram on raw image
		np_img = np.array(image)
		lbp1 = mahotas.features.lbp(np_img, 1, 8, ignore_zeros=False)
		#print lbp1.ndim, lbp1.size
		print "LBP Histogram: ", lbp1
		print "LBP Length:", len(lbp1)
		f_handle = open(data_filename, 'a')
		for i in range(len(lbp1)):
			f_handle.write(str(lbp1[i]))
			f_handle.write(" ")
		f_handle.write(',')
		f_handle.close()
		print "Image has multiple color bands...Splitting Bands...."
		Red_Band, Green_Band, Blue_Band = image.split()
		print "Calculating Histogram for I3 pixels of image..."
		I3_Histogram = CalcHistogram(Green_Band)
		#save I3 Histogram to file in certain format
		print "saving I3 histogram to dictionary..."
		f_handle = open(data_filename, 'a')
		for i in range(len(I3_Histogram)):
			f_handle.write(str(I3_Histogram[i]))
			f_handle.write(" ")
		f_handle.write(',')
		f_handle.close()
		#calculate RGB histogram on raw image
		rgb_histo = image.histogram()
		print "saving RGB histogram to dictionary..."
		f_handle = open(data_filename, 'a')
		for i in range(len(rgb_histo)):
			f_handle.write(str(rgb_histo[i]))
			f_handle.write(" ")
		f_handle.write(',')
		f_handle.close()	
	
		#calculate I3 meterics
		I3_sum =    ImageStat.Stat(image).sum
		I3_sum2 =   ImageStat.Stat(image).sum2
		I3_median = ImageStat.Stat(image).median
		I3_mean =   ImageStat.Stat(image).mean
		I3_var =    ImageStat.Stat(image).var
		I3_stddev = ImageStat.Stat(image).stddev
		I3_rms =    ImageStat.Stat(image).rms
		print "saving I3 meterics to dictionary..."
		f_handle = open(data_filename, 'a')

		print "sum img1_I3: ",    I3_sum[1]
		print "sum2 img1_I3: ",   I3_sum2[1]
		print "median img1_I3: ", I3_median[1]
		print "avg img1_I3: ",    I3_mean[1]
		print "var img1_I3: ",    I3_var[1]
		print "stddev img1_I3: ", I3_stddev[1]
		print "rms img1_I3: ",    I3_rms[1]
		#print "extrema img1_I3: ", ImageStat.Stat(img1_I3).extrema
		#print "histogram I3: ", len(img1_I3.histogram())

		f_handle.write(str(I3_sum[1]))
		f_handle.write(",")
		f_handle.write(str(I3_sum2[1]))
		f_handle.write(",")
		f_handle.write(str(I3_median[1]))
		f_handle.write(",")
		f_handle.write(str(I3_mean[1]))
		f_handle.write(",")
		f_handle.write(str(I3_var[1]))
		f_handle.write(",")
		f_handle.write(str(I3_stddev[1]))
		f_handle.write(",")
		f_handle.write(str(I3_rms[1]))
		#f_handle.write(",")
		f_handle.write('\n')
		f_handle.close()
	else:
		print "image not valid for processing: ", filename1
		time.sleep(5)
	return

def rgbToI3(r, g, b):
	"""Convert RGB color space to I3 color space
	@param r: Red
	@param g: Green
	@param b: Blue
	return (I3) integer 
	"""
	i3 = ((2*g)-r-b)/2	 
	return i3

def rgb2I3 (img):
	"""Convert RGB color space to I3 color space
	@param r: Red
	@param g: Green
	@param b: Blue
	return (I3) integer 
	"""
	xmax = img.size[0]
	ymax = img.size[1]
	#make a copy to return
	returnimage = Image.new("RGB", (xmax,ymax))
	imagearray = img.load()
	for y in range(0, ymax, 1):					
		for x in range(0, xmax, 1):
			rgb = imagearray[x, y]
			i3 = ((2*rgb[1])-rgb[0]-rgb[2]) / 2
			#print rgb, i3
			returnimage.putpixel((x,y), (0,i3,0))
	return returnimage

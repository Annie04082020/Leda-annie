import argparse
import os
import glob
import xml.dom.minidom
import cv2

def find_imgs_correspond_xml(xml_files):
	img_format = ['.jpg', '.bmp', '.png', '.jpeg', '.JPG', '.PNG', '.BMP', 'JPEG', '.tiff']
	img_files = []
	for xml_n in xml_files:
		img_list = [xml_n[:-4] + s for s in img_format]
		for img_path in img_list:
			if os.path.exists(img_path):
				img = img_path
				img_files.append(img)
				break
	return img_files

def get_file_name(input_folder):
	xml_files = glob.glob(os.path.join(input_folder, "*.xml"))
	img_files = find_imgs_correspond_xml(xml_files)
	return xml_files, img_files

def crop_label(xml_file, img_file, output_folder):
	basename = os.path.splitext(os.path.basename(img_file))
	img = cv2.imread(img_file)
	dom = xml.dom.minidom.parse(xml_file)
	root = dom.documentElement
	# filename = root.getElementsByTagName('filename')
	object_all = root.getElementsByTagName('name')
	xmin = root.getElementsByTagName('xmin')
	ymin = root.getElementsByTagName('ymin')
	xmax = root.getElementsByTagName('xmax')
	ymax = root.getElementsByTagName('ymax')
	# nodes = dom.getElementsByTagName("object")
	# width = root.getElementsByTagName('width')
	# height = root.getElementsByTagName('height')
	bboxes = []
	class_labels = []
	for j in range(len(object_all)):
		bboxes.append([int(xmin[j].firstChild.data), int(ymin[j].firstChild.data), int(xmax[j].firstChild.data), int(ymax[j].firstChild.data)])
		class_labels.append(object_all[j].firstChild.data)

	for i in range(len(class_labels)):
		img_crop = img[bboxes[i][1]:bboxes[i][3], bboxes[i][0]:bboxes[i][2]]
		save_path = os.path.join(output_folder, class_labels[i] + '_' + basename[0] + '_' + str(i) + basename[1])
		cv2.imwrite(save_path,img_crop)

	return bboxes, class_labels

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = 'crop label images.')
    parser.add_argument('-i', '--input_folder', type = str, default=None,
        help = 'The folder of the images and xml files.')
    parser.add_argument('-o', '--output_folder', type = str, default=None,
        help = 'The folder save the crop images.')
    parameters = vars(parser.parse_args())
    input_folder = parameters['input_folder']
    output_folder = parameters['output_folder']

    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    xml_files, img_files = get_file_name(input_folder)
    for indx in range(len(img_files)):
    	crop_label(xml_files[indx], img_files[indx], output_folder)
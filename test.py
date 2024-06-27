from ui import ocr_it

cut_pics = ['D:\\aProject\\py\\myDeepdoc\\input\\img.png']
input_file = r'D:\aProject\py\myDeepdoc\input\img.png'
threshold = 0.7
mode = 'tsr'
ocr_it(input_file, threshold, mode, cut_pics)

from ui import ocr_it

cut_pics = ['C:\\Users\\liuch\\AppData\\Local\\Temp\\gradio\\cf9a194b5f45af432d6bef89c2c80b234c4cce08\\img.png']
input_file = r'C:\Users\liuch\Pictures\mj-01\img.png'
threshold = 0.7
mode = 'tsr'
ocr_it(input_file, threshold, mode, cut_pics)

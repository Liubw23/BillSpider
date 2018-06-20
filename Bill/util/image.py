import pytesseract
from PIL import Image

tessdata_dir_config = '--tessdata-dir "C:\\Program Files (x86)\\Tesseract-OCR\\tessdata"'


def recognize_image(img_path):
    image = Image.open(img_path)
    code = pytesseract.image_to_string(image, config=tessdata_dir_config, lang='chi_sim')
    print(code)
    return code


def get_bin_table(threshold=130):
    # 获取灰度转二值的映射table
    table = []
    for i in range(256):
        if i < threshold:
            table.append(0)
        else:
            table.append(1)
    return table


def read_image():
    image = Image.open('code.jpg')
    imgry = image.convert('L')  # 转化为灰度图
    table = get_bin_table()
    out = imgry.point(table, '1')

    text = pytesseract.image_to_string(out, config=tessdata_dir_config)
    # 去除数字以外的其他字符
    fil = filter(str.isdigit, text)
    new_text = ''
    for i in fil:
        new_text += i
    print(new_text)

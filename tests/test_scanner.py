from utils import scanner
import cv2


print(scanner.get_passport_data(cv2.imread("images/passports_full/passport_2.jpg")))

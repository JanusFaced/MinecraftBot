from pathlib import Path
import numpy as np
import time
import os
import mss
import cv2
import subprocess

import logging
import make_logger

current_file_path = Path(__file__).resolve()
current_dir = current_file_path.parent

os.environ['LEVEL_CONFIG'] = 'INFO'
os.environ['WAY_TO_LOG_JOURNAL'] = str(current_dir/'logs'/'log_journal.log')
os.environ['WAY_EXTRACT_FILES'] = str(current_dir/'extract_files')

make_logger.make()
logger = logging.getLogger('DATAMINER:dms')

def get_mouse_position():
    result = subprocess.run(
    	['xdotool', 'getmouselocation'],
    	capture_output=True,
    	text=True
    )

    parts = result.stdout.strip().split()
    x = int(parts[0].split(':')[1])
    y = int(parts[1].split(':')[1])

    return [x, y]

def click_clack():
	before = get_mouse_position()
	logger.info(f"Before click: {before}")

	subprocess.run(['xdotool', 'click', '3'])

	time.sleep(0.2)

	after = get_mouse_position()
	logger.info(f"After click: {after}")

def main():

	monitor_number=1
	add_top = 1024
	add_left = 1280

	with mss.MSS() as sct:
		monitor = sct.monitors[monitor_number]
		screen_width = monitor['width']
		screen_height = monitor['height']

	logger.info(f'screen_width = {screen_width} | screen_height = {screen_height}')

	lower_red_white = np.array([0, 0, 100])  # Нижняя граница красного/белого
	upper_red_white = np.array([255, 255, 255])  # Верхняя граница красного/белого

	size_of_window = 0.175

	with mss.MSS() as sct:

		logger.info('Start? Enter "Enter" for continue!')
		input()

		# Создаем окно с возможностью изменения размеров
		cv2.namedWindow("Frame", cv2.WINDOW_NORMAL)
		cv2.moveWindow("Frame", -500, 100)

		for i in range(10):
			value_second = 10 - i
			logger.info(f'Start after {value_second} seconds...')
			time.sleep(1)

		#Произведение первого действия
		click_clack()
		time.sleep(3)

		#Поиск объекта
		width = int(screen_width*0.10)
		height = int(screen_height*0.25)
		top = add_top + int(screen_height*0.30) - height//2
		left = add_left + int(screen_width*0.50) - width//2

		monitor = {
			"top": top,
			"left": left,
			"width": width,
			"height": height
		}

		frame = np.array(sct.grab(monitor))
		frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
		mask = cv2.inRange(frame, lower_red_white, upper_red_white)
		contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		largest_contour = max(contours, key=cv2.contourArea)
		x, y, w, h = cv2.boundingRect(largest_contour)
		primary_center_x, primary_center_y = x + w//2, y + h//2  # Центр объекта

		center_x = primary_center_x + left
		center_y = primary_center_y + top

		logger.info(f'x: {center_x} | y: {center_y}')
		cv2.imshow("Frame", frame)
		cv2.waitKey(1)

		time.sleep(3)

		#Определение рабочего монитора
		width = int(screen_width*size_of_window)
		height = int(screen_height*size_of_window)
		top = center_y - int(height/2)
		left = center_x - int(width/2)

		monitor = {
			"top": top,
			"left": left,
			"width": width,
			"height": height
		}

		my_event = False
		ma_count = 0
		multiple_channel = 3
		work_average_window = 50
		min_count = 1000
		average_value_list = []
		average_delta_list = []
		average_value = 0
		average_delta = 0

		while True:

			ma_count += 1

			frame = np.array(sct.grab(monitor))
			frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
			mask = cv2.inRange(frame, lower_red_white, upper_red_white)

			#stream_value
			stream_value = np.sum(mask > 0)

			#average_value
			average_value_list.append(stream_value)
			if len(average_value_list) >= min_count:
				average_value_list = average_value_list[1:]
			average_value = np.mean(average_value_list)

			#stream_delta
			stream_delta = stream_value - average_value

			#average_delta
			abs_delta = abs(stream_delta)
			average_delta_list.append(abs_delta)
			if len(average_delta_list) >= min_count:
				average_delta_list = average_delta_list[1:]
			average_delta = np.mean(average_delta_list)

			#Границы рабочего канала
			max_board = average_value + multiple_channel*average_delta
			min_board = average_value - multiple_channel*average_delta

			#Рабочее сглаженное значение
			work_average_stream_value = np.mean(average_value_list[-work_average_window:])

			if (ma_count > 3*min_count):

				s_v = int(stream_value)
				w_a_s_v = int(work_average_stream_value)
				a_v = int(average_value)
				a_d = int(average_delta)

				maxBoard = int(max_board)
				minBoard = int(min_board)

				logger.info(f's: max[{maxBoard}] | {s_v} ({w_a_s_v}) | min[{minBoard}] | as: {a_v} | d: {a_d} | wma {ma_count}')

				# Если объект выходит за диапазона канала колебаний
				if (work_average_stream_value < min_board):
					my_event = True
					logger.info("Объект пропал! Выполняем действие.")

				if my_event:
					click_clack()
					time.sleep(2)
					click_clack()
					time.sleep(2)
					my_event = False
					average_delta_list = []
					ma_count = 0
					logger.info(f'clear => average_delta_list = {average_delta_list} | ma_count = {ma_count}')

			else:
				logger.info(f'window_ma {ma_count}')

			cv2.imshow("Frame", frame)

			if cv2.waitKey(1) & 0xFF == ord("q"):
				break

		cv2.destroyAllWindows()

try:
	main()

except Exception as error_body:
	logger.critical('Critical error!!!', exc_info=True)


#!/usr/bin/env python3
# coding: utf-8
# Button configuration File

button_rows =2 
button_colums = 4
root_location = "/button_sounds/"
button_config_sound =  [[0 for i in range(button_rows)] for j in range(button_colums)]
button_config_sound[0][0] = root_location+"milk_นม.wav"
button_config_sound[1][0] = root_location+"water_น้ำ.wav"
button_config_sound[2][0] = root_location+"snack_ขนม.wav"
button_config_sound[3][0] = root_location+"play_Pim_เล่น.wav"
button_config_sound[0][1] = root_location+"yes_ใช่.wav"
button_config_sound[1][1] = root_location+"no_ไม่ใช่.wav"
button_config_sound[2][1] = root_location+"ThankYou_ขอบคุณ.wav"
button_config_sound[3][1] = root_location+"mum_แม่.wav"
print (button_config_sound)
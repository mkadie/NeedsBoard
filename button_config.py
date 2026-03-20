#!/usr/bin/env python3
# coding: utf-8
# Button configuration File

button_rows = 2
button_columns = 4
root_location = "/button_sounds/"
button_sound = [0 for i in range(button_rows * button_columns + 1)]
button_sound[0] = root_location + "thirsty.mp3"
button_sound[1] = root_location + "hungry.mp3"
button_sound[2] = root_location + "more.mp3"
button_sound[3] = root_location + "bathroom.mp3"
button_sound[4] = root_location + "stinky.mp3"
button_sound[5] = root_location + "yes.mp3"
button_sound[6] = root_location + "no.mp3"
button_sound[7] = root_location + "please.mp3"
button_sound[8] = root_location + "read.mp3"

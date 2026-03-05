import os
import random
import json

with open('words.json', 'r', encoding='utf-8') as f:
	aa = json.load(f)
	for b in aa:
		print(b)
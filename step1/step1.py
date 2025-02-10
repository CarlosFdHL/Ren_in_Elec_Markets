from model.py import step1_model
from input_data import *

input_data = InputData(generators)

model = step1_model(input_data)
model.run()
model.print_results()
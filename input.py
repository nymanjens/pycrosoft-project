from collections import OrderedDict
from settings import *

FILE = "input.csv"

def get_tasks():
	f = open(FILE, 'U')
	input_file = f.readlines()
	f.close()
	tasks = OrderedDict()
	headers = input_file[0].strip().split(';')
	ind = [headers.index(used_header) for used_header in USED_HEADERS]
	ind.append(max(ind)+1)
	resource_ind = [ind[4]+i for i, header in enumerate(headers[ind[4]:]) if header.partition('[')[0]]
	avail_resources = {}
	for i in resource_ind:
		header, _, amount = headers[i].partition('[')
		try:
			avail_resources[header] = float(amount.partition(']')[0])
		except ValueError:
			avail_resources[header] = -1
	for line in input_file[1:]:
		split_line = line.strip().split(';')
		if any(split_line):
			task = {
				'ID':split_line[ind[0]],
				'label': split_line[ind[1]],
				'precedences':[precedence for precedence in split_line[ind[2]].split(',')] if split_line[ind[2]]!='' else [],
				'duration':int(split_line[ind[3]]),
				'resources':{}}
			for i in resource_ind:
				if float(split_line[i]):
					task['resources'][headers[i].partition('[')[0]] = float(split_line[i])
			tasks[split_line[ind[0]]] = task
	# input check
	for t in tasks.values():
		resources = task['resources']
		if 'G' in resources:
			for rid in GENERAL_CATEGORY:
				assert not rid in resources, "'G' resource cannot be on same task as individual general category resources"
		for rid in GENERAL_CATEGORY:
			if rid in resources:
				for rid2 in GENERAL_CATEGORY:
					if rid != rid2:
						assert not rid2 in resources, "different individual general category resources should not be on same task"
	# return
	return tasks, avail_resources

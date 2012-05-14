import time
import numpy as np
import pylab as pl
from pprint import pprint
from scheduling import resourceScheduling
from input import get_tasks
import output
try: import cPickle as pickle
except: import pickle

def main():
	### get tasks ###
	tasks, avail_resources = get_tasks()
	#print "Tasks:\n", pprint(tasks.items())
	
	### create chedule ###
	res_sch = resourceScheduling(tasks, avail_resources)
	schedule = res_sch.get_schedule_from_many_simulations(1e2)
	
	### apply CC/BM ###
	res_sch.CCBM_schedule_alap_and_calc_slack()
	res_sch.CCBM_put_buffers()
	
	### final step: divide general resources ###
	res_sch.divide_general_resource()
	
	### preprocess schedule for output ###
	for sch_props, task in zip(schedule.values(), tasks.values()):
		sch_props['end'] = res_sch.task_end(task)
	
	### output ###
	pickle.dump(res_sch, open('result.pkl','w'))

if __name__=='__main__':
	main()
	### output ###
	res_sch = pickle.load(open('result.pkl'))
	print 'project duration:', res_sch.duration()
	output.save_to_gantt(res_sch)
	output.save_to_gantt2(res_sch)
	# plots
	pl.ion()
	output.plot_resources('MW', res_sch)
	pl.figure(); output.plot_resources('PR', res_sch)
	pl.ioff()
	pl.figure(); output.plot_resources('FR', res_sch)

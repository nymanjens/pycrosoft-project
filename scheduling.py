import numpy as np
import pylab as pl
from copy import copy
from collections import OrderedDict
import random
from settings import *
from progressbar import ProgressBar

class resourceScheduling:
	def __init__(self, tasks, avail_resources=None):
		self.tasks = tasks
		self.max_duration = self._max_duration()
		self.resources_left = {}
		self.schedule = OrderedDict()
		self.avail_resources = avail_resources if avail_resources!=None else AVAIL_RESOURCES
		self.reset()
	
	def reset(self):
		for key in self.avail_resources:
			self.resources_left[key] = np.ones(self.max_duration) * self.avail_resources[key]
		for task_ID in self.tasks:
			self.schedule[task_ID] = {'start':None}
		
	
	def _max_duration(self):
		duration = 0
		for task_ID in self.tasks:
			duration += self.tasks[task_ID]['duration']
		return duration
	
	def duration(self):
		return max(self.task_end(task) for task in self.tasks.values()) + 1
	
	def resource_usage(self, resource_ID):
		resources_left = self.resources_left[resource_ID]
		resources_available = self.avail_resources[resource_ID]
		return resources_available - resources_left
	
	def get_random_priority_list(self):
		precedence_list, task_IDs, precedence_count = [], [], []
		for task_ID in self.tasks:
			precedence_list.append(copy(self.tasks[task_ID]['precedences']))
			task_IDs.append(task_ID)
			precedence_count.append(len(precedence_list[-1]))
		
		priority_list = []
		while(len(priority_list)!=len(self.tasks)):
			possible_choices = np.where(np.array(precedence_count)==0)[0]
			choice = random.choice(possible_choices)
			for i, task_ID in enumerate(task_IDs):
				try:
					precedence_list[i].remove(task_IDs[choice])
				except ValueError:
					pass
				else:
					precedence_count[i] -= 1
			priority_list.append(task_IDs[choice])
			precedence_list.pop(choice)
			task_IDs.pop(choice)
			precedence_count.pop(choice)
		return priority_list
		
	def get_schedule_from_many_simulations(self, N=1000):
		minimizer = Minimizer()
		progress = ProgressBar()
		for n in progress(xrange(int(N))):
			priority_list = self.get_random_priority_list()
			self.generate_schedule_from(priority_list)
			cost = self.duration()
			minimizer.add(priority_list, cost)
		self.best_priority_list = minimizer.argmin
		#minimizer.plot()
		self.generate_schedule_from(self.best_priority_list)
		return self.schedule
	
	def generate_schedule_from(self, priority_list):
		self.reset()
		for task_ID in priority_list:
			task = self.tasks[str(task_ID) if not isinstance(task_ID,str) else task_ID]
			for i in range(self.max_duration):
				if self.is_valid(i,task):
					self.plan(i,task)
					break
			if i>=self.max_duration-1:
				raise Exception("impossible schedule")
	
	def is_valid(self, i, task):
		return self.is_precedence_valid(i, task) and self.is_resource_valid(i, task)
	
	def is_precedence_valid(self, i, task):
		for prec_task_ID in task['precedences']:
			prec_task = self.tasks[prec_task_ID]
			prec_task_end = self.task_end(prec_task)
			if prec_task_end==None:
				raise Exception("task is being scheduled before precedence task is scheduled")
			if prec_task_end >= i:
				return False
		return True
		
	def is_resource_valid(self, i, task, write=False):
		j = i + task['duration']
		for resource_ID in task['resources']:
			resource = task['resources'][resource_ID]
			if resource_ID=='G':
				general_resources_used = self.avail_resources['G'] - self.resources_left['G'][i:j]
				resources_left = -general_resources_used
				for resid in GENERAL_CATEGORY:
					resources_left += self.resources_left[resid][i:j]
				# check if enough resources left
				if any(resources_left - resource < 0):
					return False
				if write:
					self.resources_left['G'][i:j] -= resource
					self.update_general_resource_division(i, j)
			else:
				resources_left = self.resources_left[resource_ID][i:j]
				if resource > self.avail_resources[resource_ID]:
					return False
					# Jens: niet nodig, kan als aparte resource aangeuid worden in input 
					#resource_MW = resource-resources_left # Robin: voorkeur geven aan gebruik van vrijwilligers of niet?
					#resource = resources_left
					#resource_MW_left = self.resources_left['MW'][i:j]
					#if any(resource_MW_left-resource_MW < 0):
					#	return False
					#if write:
					#	self.resources_left['MW'][i:j] -= resource_MW
				elif any(resources_left - resource < 0):
					return False
				if write:
					self.resources_left[resource_ID][i:j] -= resource
					self.update_general_resource_division(i, j)
		return True
	
	def print_all(self, i, j):
		for rid in ('G', 'FR', 'PR'):
			print rid,': ', self.resources_left[rid][i:j]
	
	def update_general_resource_division(self, i, j):
		""" checks if general resources are used that much that an individual resource can no longer fully be used """
		general_resources_used = self.avail_resources['G'] - self.resources_left['G'][i:j]
		for resid in GENERAL_CATEGORY:
			available_in_others = np.zeros(general_resources_used.shape)
			for accumresid in GENERAL_CATEGORY:
				if accumresid != resid:
					available_in_others += self.resources_left[accumresid][i:j]
			if any(available_in_others < general_resources_used):
				diff = general_resources_used - available_in_others
				diff = np.array([d if d > 0 else 0 for d in diff])
				self.resources_left[resid][i:j] -= diff
				assert all(self.resources_left[resid][i:j] >= 0), "resid={}, resleft={}".format(resid,self.resources_left[resid][i:j])
				self.resources_left['G'][i:j] += diff
				return self.update_general_resource_division(i, j)
	
	def divide_general_resource(self):
		""" divide general resources for final usage """
		### divide G for every timestep ##
		for i in range(self.max_duration):
			general_resources_used = self.avail_resources['G'] - self.resources_left['G'][i]
			while general_resources_used:
				resources_left = [self.resources_left[resid][i] for resid in GENERAL_CATEGORY if self.resources_left[resid][i]]
				smallest_val = min(resources_left)
				smallest_ind = resources_left.index(smallest_val)
				reduction = min(smallest_val*len(resources_left), general_resources_used)
				for resid in GENERAL_CATEGORY:
					self.resources_left[resid][i] -= reduction/float(len(resources_left)) if self.resources_left[resid][i] else 0
				general_resources_used -= reduction
		
		### recalculate G (for analysis only) ###
		self.resources_left['G'] = np.array([self.resources_left[resid] for resid in GENERAL_CATEGORY]).sum(0)
	
	def plan(self, i, task):
		assert self.is_resource_valid(i, task, write=True), 'i={}, task={}'.format(i,task)
		self.schedule[task['ID']]['start'] = i
	
	def move(self, task, i):
		self.schedule[task['ID']]['start'] = i
		self.refresh_resource_usage()
		assert self.is_valid_schedule()
	
	def refresh_resource_usage(self):
		# reset resource usage
		for key in self.avail_resources:
			self.resources_left[key] = np.ones(self.max_duration) * self.avail_resources[key]
		# plan tasks, using priority list
		for task_ID in self.best_priority_list:
			task = self.tasks[task_ID]
			sched = self.schedule[task_ID]
			self.plan(sched['start'], task)
		
	def task_end(self, task):
		start = self.schedule[task['ID']]['start']
		return start + task['duration'] - 1 if start!=None else None
	
	def is_valid_schedule(self):
		# check resources
		dummy_task = {
			'duration': self.max_duration,
			'resources': dict(zip(self.avail_resources.keys(), np.zeros(len(self.avail_resources)))),
		}
		if not self.is_resource_valid(0, dummy_task):
			return False
		# check precedences
		for tid in self.best_priority_list:
			t = self.tasks[tid]
			s = self.schedule[tid]
			if not self.is_precedence_valid(s['start'], t):
				return False
		return True
	
	""" CCBM-specific functions """
	def CCBM_schedule_alap_and_calc_slack(self):
		invpriority_list = [x for x in reversed(self.best_priority_list)]
		for task_ID in invpriority_list:
			task = self.tasks[task_ID]
			sched = self.schedule[task_ID]
			task_end = self.task_end(task)
			delta_i = 0
			for delta_i in range(1, self.duration() - task_end):
				i = task_end + delta_i
				# check resource slack
				minitask = {
					'duration': 1,
					'resources': task['resources'],
				}
				if not self.is_resource_valid(i, minitask):
					delta_i -= 1
					break
				# check precedence slack
				task['duration'] += delta_i
				valid_precedence = True
				for tid in invpriority_list:
					t = self.tasks[tid]
					s = self.schedule[tid]
					if not self.is_precedence_valid(s['start'], t):
						valid_precedence = False
						break
				task['duration'] -= delta_i
				if not valid_precedence:
					delta_i -= 1
					break
				
			slack = delta_i
			sched['slack'] = slack
			self.move(task, sched['start'] + slack)
	
	def CCBM_put_buffers(self):
		### feeding buffers at the feeding chains ###
		for task_ID in self.best_priority_list:
			task = self.tasks[task_ID]
			sched = self.schedule[task_ID]
			task_start = sched['start']
			slack = sched['slack']
			if not slack:
				continue
			delta = min(slack, FEEDING_BUFFER)
			self.move(task, task_start - delta)
		### project buffer at the end ###
		CC_len = self.duration()
		self.tasks['99'] = {
			'ID': '99',
			'label': "Project buffer",
			'precedences': self.tasks.keys(),
			'duration': int(round(CC_len * PROJECT_BUFFER / 100.)),
			'resources': {},
		}
		self.schedule['99'] = {
			'start': CC_len,
			'slack': 0,
		}
		assert self.is_valid_schedule()

class Minimizer:
	argmin = None
	mincost = float('inf')
	PLOT = False
	history = None
	def add(self, arg, cost):
		if self.PLOT:
			if not self.history:
				self.history = []
			self.history.append(cost)
		if cost < self.mincost:
			self.mincost = cost
			self.argmin = arg
	def plot(self):
		pl.plot(self.history)
		pl.show()



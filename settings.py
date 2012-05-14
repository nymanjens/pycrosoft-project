# defines the resource availability
AVAIL_RESOURCES = {
	'PR': 4,
	'FR': 4,
	'G': -1, # general category, the availability is further initialized as the sum of the available resources
	'MW': 20 # volunteers
}

USED_HEADERS = ['task_ID', 'task_name', 'precedences', 'duration']

# defines which resources can use general category
GENERAL_CATEGORY = ['PR', 'FR']

# init G avail as the sum of the available resources
AVAIL_RESOURCES['G'] = sum(AVAIL_RESOURCES[res] for res in GENERAL_CATEGORY)

# CCBM settings
PROJECT_BUFFER = 30 #percent of total duration
FEEDING_BUFFER = 5 #days

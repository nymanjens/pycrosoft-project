from __future__ import division
import numpy as np
import pylab as pl
from jinja2 import Environment, FileSystemLoader
from copy import copy
import datetime
from settings import *

""" RESOURCE PLOT """
def plot_resources(resource_ID, res_sch, avail_resources=None):
    duration = res_sch.duration()
    threshold = avail_resources[resource_ID] if avail_resources!=None else AVAIL_RESOURCES[resource_ID]
    res_usage = res_sch.resource_usage(resource_ID)[:duration]
    bar_border = [];
    for n, height in enumerate(res_usage):
        bar_border.append([n, height])
        bar_border.append([n+1, height])
    pl.bar(np.arange(len(res_usage)), res_usage, width=1, color='r', linewidth=0)
    pl.axhline(threshold)
    x,y = np.array(bar_border).T
    pl.plot(x,y, '-k')
    pl.ylim([0, threshold+1])
    pl.xlim([0, duration])
    pl.xlabel('Day number')
    pl.ylabel('%s usage' % resource_ID)
    pl.show()

""" GANTT CHART """
def days(d):
    return datetime.timedelta(days = d)

def save_to_gantt(res_sch):
    ### vars ###
    tasks = res_sch.tasks
    schedule = res_sch.schedule
    total_duration = res_sch.duration()
    
    ### get start and end dates ###
    end_date = datetime.date(2013, 4, 13)
    start_date = end_date - days(total_duration)
    schedule = copy(schedule)
    for sch_props, task in zip(schedule.values(), tasks.values()):
        sch_props['start_date'] = start_date + days(sch_props['start'])
        sch_props['end_date'] = sch_props['start_date'] + days(task['duration']-1)
    
    ### get and save xml ###
    xml = ""
    xml += "<project>\n"
    for sch_props, task in zip(schedule.values(), tasks.values()):
        xml += """
          <task>
            <pID>%(id)s</pID>
            <pName>%(label)s</pName>
            <pStart>%(start)s</pStart>
            <pEnd>%(end)s</pEnd>
            <pColor>%(color)s</pColor>
            <pMile>0</pMile>
            <pRes></pRes>
            <pComp>0</pComp>
            <pParent>0</pParent>
            <pOpen>1</pOpen>
            <pDepend />
          </task>
        """ % {
            'id': task['ID'],
            'label': task['label'],
            'start': sch_props['start_date'].strftime("%d/%m/%Y"),
            'end': sch_props['end_date'].strftime("%d/%m/%Y"),
            'color': '0000ff' if sch_props['slack'] else 'ff0000' if not task['ID']=='99' else '00ff00',
        }
    xml += "</project>\n"
    open('output/gantt.xml', 'w').write(xml)


""" GANTT CHART 2 """
### settings ###
WIDTH = 1000 #px

def px(x):
    return int(round(WIDTH * x))

def save_to_gantt2(res_sch):
    ### vars ###
    tasks = res_sch.tasks
    schedule = res_sch.schedule
    total_duration = res_sch.duration()
    ### preprocess schedule ###
    schedule = copy(schedule)
    for sch_props, task in zip(schedule.values(), tasks.values()):
        sch_props['start_px'] = px(sch_props['start'] / total_duration)
        sch_props['width_px'] = px(task['duration'] / total_duration)
        sch_props['end_px'] = sch_props['start_px'] + sch_props['width_px']
        sch_props['color'] = 'blue' if sch_props['slack'] else 'red' if not task['ID']=='99' else '#00FF00'
        sch_props['label'] = task['label']
    ### get weeks ###
    weeks = []
    for n in range(int(np.ceil(total_duration/7))):
        week = {
            'num': n + 1,
            'start_px': px(7*n / total_duration),
            'end_px': px(min(1, 7*(n+1) / total_duration)),
        }
        week['width_px'] = week['end_px'] - week['start_px'] - 1
        weeks.append(week)
    weeks[-1]['width_px'] += 2
    ### apply jinja2 template ###
    env = Environment(loader=FileSystemLoader('output/templates'))
    template = env.get_template('gantt2.html')
    html = template.render(
        WIDTH = WIDTH,
        schedule = schedule.items(),
        weeks = weeks,
        numweeks = len(weeks),
    )
    open('output/gantt2.html', 'w').write(html)




import htcondor
import classad
import json
from flask import Flask, jsonify, request

app = Flask(__name__)

def convert(input):
    """Convert ClassAd-specific values into strings"""
    if input == classad.Value.Undefined:
        return str(input)
    return input

def jobs_list(attrs, constraint, completed):
    """Generate list of jobs"""
    schedd = htcondor.Schedd()
    if not completed:
        jobs = schedd.xquery(constraint, attrs)
    else:
        jobs = schedd.history(constraint, attrs)
    list = []
    for job in jobs:
        list.append({attr:convert(job.lookup(attr).eval()) for attr in job.keys()})
    return list

def jobs_overview(constraint):
    """Generate job overview"""
    schedd = htcondor.Schedd()
    jobs = schedd.xquery(constraint, ['JobStatus'])
    data = {}
    for job in jobs:
        data[job['JobStatus']] = 1 if job['JobStatus'] not in data else data[job['JobStatus']] + 1
    map = {1:'Idle', 2:'Running', 3:'Removed', 4:'Completed', 5:'Held'}
    overview = {map[status]:value for status, value in data.items()}
    return overview

def machines_list(attrs, constraint):
    """Generate a list of machines"""
    coll = htcondor.Collector()
    startds = coll.query(htcondor.AdTypes.Startd, constraint, attrs)
    list = []
    for startd in startds:
        list.append({attr:convert(startd.lookup(attr).eval()) for attr in startd.keys()})
    return list

def machines_overview(constraint):
    """Generate an overview of machines"""
    coll = htcondor.Collector()
    startds = coll.query(htcondor.AdTypes.Startd, constraint, ['State'])
    overview = {'Owner':0, 'Unclaimed':0, 'Matched':0, 'Claimed':0, 'Preempting':0, 'Drained':0}
    for startd in startds:
        overview[startd['State']] += 1
    return overview

@app.route("/htcondor/v1/machines", methods=['GET'])
@app.route("/htcondor/v1/machines/<machine>", methods=['GET'])
def machine(machine=None):
    user_attrs = []
    if 'attrs' in request.args:
        user_attrs = str(request.args['attrs']).split(',')

    if machine == None and 'list' in request.args:
        attrs = ['Name', 'OpSys', 'Arch', 'State', 'Activity', 'LoadAvg', 'TotalMemory']
        if len(user_attrs) > 0:
            attrs = user_attrs
        constraint = 'True'
        return jsonify(machines_list(attrs, constraint))
    elif machine != None:
        attrs = []
        if len(user_attrs) > 0:
            attrs = user_attrs
        constraint = 'Machine =?= "%s"' % str(machine)
        return jsonify(machines_list(attrs, constraint))
    return jsonify(machines_overview('True'))

@app.route("/htcondor/v1/jobs", methods=['GET'])
@app.route("/htcondor/v1/jobs/<job>", methods=['GET'])
def jobs(job=None):
    user_attrs = []
    if 'attrs' in request.args:
        user_attrs = str(request.args['attrs']).split(',')

    completed = False
    if 'completed' in request.args:
        completed = True

    if job == None and 'list' in request.args:
        attrs = ['ClusterId', 'ProcId', 'Owner', 'JobStatus', 'Cmd', 'Args', 'JobPrio', 'ResidentSetSize', 'QDate']
        if len(user_attrs) > 0:
            attrs = user_attrs
        constraint = 'True'
        return jsonify(jobs_list(attrs, constraint, completed))
    elif job != None:
        attrs = []
        if len(user_attrs) > 0:
            attrs = user_attrs
        constraint = 'ClusterId =?= %d' % int(job)
        return jsonify(jobs_list(attrs, constraint, completed))
    return jsonify(jobs_overview('True'))

@app.route("/htcondor/v1/jobs", methods=['POST'])
def create_job():
    job = {str(item):str(value) for item, value in request.get_json().items()}
    sub = htcondor.Submit(job)
    schedd = htcondor.Schedd()
    with schedd.transaction() as txn:
        id = sub.queue(txn)
    return jsonify({'ClusterId': id}), 201

@app.route("/htcondor/v1/jobs/<int:job>", methods=['DELETE'])
def delete_job(job):
    schedd = htcondor.Schedd()
    ret = schedd.act(htcondor.JobAction.Remove, 'ClusterId == %d' % job)
    if ret['TotalSuccess'] > 0:
        return '', 200
    return '', 400

if __name__ == "__main__":
    app.run()
    

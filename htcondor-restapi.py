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


def classad_to_json(input):
    """Convert a ClassAd into a JSON-compatible dict"""
    return {attr:convert(input.lookup(attr).eval()) for attr in input.keys()}


def jobs_list(attrs, constraint, completed, num):
    """Generate list of jobs"""
    schedd = htcondor.Schedd()
    if not completed:
        jobs = schedd.xquery(constraint, attrs)
    else:
        jobs = schedd.history(constraint, attrs, num)
    return [classad_to_json(job) for job in jobs]


def jobs_overview(constraint):
    """Generate job overview"""
    schedd = htcondor.Schedd()
    jobs = schedd.query(constraint, opts=htcondor.QueryOpts.SummaryOnly)[0]
    overview = {'Jobs':jobs['AllusersJobs'],
                'Running':jobs['AllusersRunning'],
                'Idle':jobs['AllusersIdle'],
                'Held':jobs['AllusersHeld'],
                'Removed':jobs['AllusersRemoved'],
                'Suspended':jobs['AllusersSuspended'],
                'Completed':jobs['AllusersCompleted']}
    return overview


def machines_list(attrs, constraint):
    """Generate a list of machines"""
    coll = htcondor.Collector()
    startds = coll.query(htcondor.AdTypes.Startd, constraint, attrs)
    return [classad_to_json(startd) for startd in startds]


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

    num = 1
    completed = False
    if 'completed' in request.args:
        completed = True
    if 'num' in request.args:
        num = int(request.args['num'])

    if job == None and 'list' in request.args:
        attrs = ['ClusterId', 'ProcId', 'Owner', 'JobStatus', 'Cmd', 'Args', 'JobPrio', 'ResidentSetSize', 'QDate']
        if len(user_attrs) > 0:
            attrs = user_attrs
        constraint = 'True'
        return jsonify(jobs_list(attrs, constraint, completed, num))
    elif job != None:
        attrs = []
        if len(user_attrs) > 0:
            attrs = user_attrs
        constraint = 'ClusterId =?= %d' % int(job)
        return jsonify(jobs_list(attrs, constraint, completed, num))
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

# HTCondor RESTful API
This is just a proof-of-concept and should not be used in production for many reasons, including:
* there is no authentication
* there is no way currently to submit input files
* there has been no attempt to handle partitionable slots in a sensible way (not that `condor_status` does this anyway)
* ...

However, it demonstrates that being able to interact with HTCondor via a RESTful API and with JSON can be very useful!

To run the code for testing only:
```
python htcondor-restapi.py
```
This should be on a machine with a schedd and Flask installed. Below `jq` is used to print JSON in a nice way.

## Machines

### Overview
Overview of the status of all machines:
```
curl -s http://localhost:5000/htcondor/v1/machines | jq .
```
> output
```json
{
  "Claimed": 1,
  "Drained": 0,
  "Matched": 0,
  "Owner": 0,
  "Preempting": 0,
  "Unclaimed": 0
}
```

### Listing machines
List machines, providing similar information to what's provided by the `condor_status` command by default:
```
curl -s http://localhost:5000/htcondor/v1/machines?list | jq .
```
> output
```json
[
  {
    "Activity": "Busy",
    "Arch": "X86_64",
    "LoadAvg": 0,
    "Name": "vnode-0.localdomain",
    "OpSys": "LINUX",
    "State": "Claimed",
    "TotalMemory": 991
  }
]
```

### More detailed information
List machines using a specified set of ClassAd attributes:
```
curl -s "http://localhost:5000/htcondor/v1/machines?list&attrs=Name,State" | jq .
```
> output
```json
[
  {
    "Name": "vnode-0.localdomain",
    "State": "Claimed"
  }
]
```

Getting the full ClassAd for a specific machine in JSON format:
```
curl -s http://localhost:5000/htcondor/v1/machines/vnode-0.localdomain | jq .
```

## Jobs

### Overview
Overview of jobs in different states:
```
curl -s http://localhost:5000/htcondor/v1/jobs | jq .
```
> output
```json
{
  "Completed": 0,
  "Held": 0,
  "Idle": 1,
  "Jobs": 2,
  "Removed": 0,
  "Running": 1,
  "Suspended": 0
}
```

### Listing jobs
List jobs, providing similar information to what's provided by the `condor_q` command by default:
```
curl -s http://localhost:5000/htcondor/v1/jobs?list | jq .
```
> output
```json
[
  {
    "Args": "4000",
    "ClusterId": 6,
    "Cmd": "/bin/sleep",
    "JobPrio": 0,
    "JobStatus": 1,
    "Owner": "cloudadm",
    "ProcId": 0,
    "QDate": 1535217842,
    "ServerTime": 1535270470
  },
  ...
]  
```

### Specifying what ClassAd attributes to return
List jobs with a specified set of ClassAd attributes:
```
curl -s "http://localhost:5000/htcondor/v1/jobs?list&attrs=Owner,ClusterId,Cmd" | jq .
```
> output
```json
[
  {
    "ClusterId": 6,
    "Cmd": "/bin/sleep",
    "Owner": "cloudadm",
    "ServerTime": 1535271450
  },
  {
    "ClusterId": "2",
    "Cmd": "/bin/sleep",
    "Owner": "cloudadm",
    "ServerTime": 1535271450
  },
  ...
]  
```
Note that "ServerTime" is provided automatically by HTCondor's python API.

### Getting a full job ClassAd
Get a full job ClassAd in JSON format:
```
curl -s http://localhost:5000/htcondor/v1/jobs/6 | jq .
```

### Completed jobs
For a completed job you need to add a parameter "completed", e.g.
```
curl -s http://localhost:5000/htcondor/v1/jobs/2?completed | jq .
```
If you don't specify a job, by default the most recently completed job will be returned. Use the parameter "num" to specify how many completed jobs to return, for example:
```
curl -s "http://localhost:5000/htcondor/v1/jobs?completed&num=4" | jq .
```

### Submitting jobs
Submit a job:
```
curl -s -X POST -H "Content-Type: application/json" \
     --data '{"executable":"/bin/sleep", "arguments":"4000"}' \
     http://localhost:5000/htcondor/v1/jobs | jq .
```
> output
```json
{
  "ClusterId": 7
}
```

### Removing jobs
To remove a job you just need to specify the cluster id:
```
curl -s -X DELETE http://localhost:5000/htcondor/v1/jobs/3
```
The status code will be 200 on success or 400 otherwise.

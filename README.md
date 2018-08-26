# HTCondor RESTful API
This is just a proof-of-concept and should not be used in production for many reasons (there is no authentication, no way to submit input files, no attempt to handle partitionable slots in a sensible way, ...). Being able to interact with HTCondor via a RESTful API and using JSON can be very useful!

To run the code for testing only:
```
python htcondor-restapi.py
```
This should be on a machine with a schedd and Flask installed. Below `jq` is used to print JSON in a nice way.

## Machines
Overview of the status of all machines:
```
curl -s http://localhost:5000/htcondor/v1/machines | jq .
```
> output
```
{
  "Claimed": 1,
  "Drained": 0,
  "Matched": 0,
  "Owner": 0,
  "Preempting": 0,
  "Unclaimed": 0
}
```
List machines, providing similar information to what's provided by the `condor_status` command by default:
```
curl -s http://localhost:5000/htcondor/v1/machines?list | jq .
```
> output
```
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
List machines using a specified set of ClassAd attributes:
```
curl -s "http://localhost:5000/htcondor/v1/machines?list&attrs=Name,State" | jq .
```
> output
```
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
Overivew of jobs:
```
curl -s http://localhost:5000/htcondor/v1/jobs | jq .
```
> output
```
{
  "Idle": 3,
  "Running": 1
}
```
List jobs, providing similar information to what's provided by the `condor_q` command by default:
```
curl -s http://localhost:5000/htcondor/v1/jobs?list | jq .
```
> output
```
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
List jobs with a specified set of ClassAd attributes:
```
curl -s "http://localhost:5000/htcondor/v1/jobs?list&attrs=Owner,ClusterId,Cmd" | jq .
```
> output
```
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
Get a full job ClassAd in JSON format:
```
curl -s http://localhost:5000/htcondor/v1/jobs/6 | jq .
```
Submit a job:
```
curl -s -X POST -H "Content-Type: application/json" \
     --data '{"executable":"/bin/sleep", "arguments":"4000"}' \
     http://localhost:5000/htcondor/v1/jobs | jq .
```
> output
```
{
  "ClusterId": 7
}
```
Delete a job:
```
curl -s -X DELETE http://localhost:5000/htcondor/v1/jobs/3
```
The status code will be 200 on success or 400 otherwise.

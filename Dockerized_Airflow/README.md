# docker-airflow

This repository contains a **Docker Compose File** of [apache-airflow](https://github.com/apache/incubator-airflow) 
for [Docker](https://www.docker.com/)'s [automated build](https://hub.docker.com/r/apache/airflow) published to the
public [Docker Hub Registry](https://registry.hub.docker.com/).

## Informations

* Based on Python (3.6-slim-buster) official Image [python:3.6-slim-buster](https://hub.docker.com/_/python/) 
  and uses the official [Postgres](https://hub.docker.com/_/postgres/) as backend and
  [Redis](https://hub.docker.com/_/redis/) as queue
* Install [Docker](https://www.docker.com/)
* Install [Docker Compose](https://docs.docker.com/compose/install/)
* Following the Airflow release from [Python Package Index](https://pypi.python.org/pypi/apache-airflow)

## Installation

Pull the image from the Docker repository.

    docker pull apache/airflow:2.0.0

## Usage

By default, docker-airflow runs Airflow with **LocalExecutor** :

    docker-compose -f docker-compose.yml up -d

NB : If you want to have DAGs example loaded (default=False), you've to set the following environment variable :

`AIRFLOW__CORE__LOAD_EXAMPLES`

in docker-compose.yml

If you want to use Ad hoc query, make sure you've configured connections:
Go to Admin -> Connections and Edit "postgres_default" set this values 
(equivalent to values in airflow.cfg/docker-compose*.yml) :
- Host : postgres
- Schema : airflow
- Login : postgres
- Password : postgres

## Notes on Docker Compose

### docker-compose Airflow
Use the empty files in the ```raw_files``` folder outside this folder to run the docker-compose. i added the airflow.cfg
file in this repository in .gitignore file as I changed it a lot.

### Troubleshooting
If you are receiving the error about the permission to the ```/opt/airflow/logs``` folder, please kindly check the 
your local airflow folder, in ```/airflow-data/``` folder, and run code below to solve the permission problem:
```shell
sudo chmod u=rwx,g=rwx,o=rwx logs
```

## Airflow Documents

These are some important questions that should be answered:
- What can you do with your Operators?
- How to change the way your task is triggered?
- How to control the number of running tasks?
- What if your task fail? 

## Operator
It is a ```task``` in your data pipeline. It is a class that encapsulating the task that you want to execute.
For example use python operator to run python codes.

Remember: **An OPERATOR Defines ONE TASK in your data pipeline**
For example do not do the cleaning and processing data both in one ```PythonOperator```. If one task failed, you should 
retry all the tasks. It means you are wasting resources and time.
So you should have: ```PythonOperator to clean data ---> PythonOperator to process data```. Try to do as much as 
possible one task one operator.

### Types of Operators
We have 3 types of operators:
- 1- Action Operators: Execute an Action, for example PythonOperator or BatchOperator
- 2- Transfer Operator: Used to transfer data from source to destination. For example mySQL to GCS operator
- 3- Sensors Operators: Wait for a condition to be met. Wait for something to happen before moving to next task. For 
  example wait for data to land on s3 then to do some tsk. **You can trigger tasks based on event.**

### Idempotency Concept
It means for an operator given the same input you should always receive the same output whenever that operator is 
triggered.
```Same Input ---> Operator ---> Same Output```
You should always inject current data at run time, in order to deal with a chunk of data at current date. To get the 
date corresponding to current Dag run, you have to access something called ```context```.

This context is defined in the task by ```provide_context=True```, you can use ```**kwargs``` in your python function
to do so. In the simpel dag below yu can see that the current date in the DAG is retrieved from the DAG contexts, 
```python
from airflow import DAG
from airflow.operators.python import PythonOperator

from datetime import datetime


default_args = {
    'start_date': datetime(2022, 5, 11)
}


def _my_func(ds):
    print(ds)


with DAG('my_dag', schedule_interval='@daily', default_args=default_args, catchup=False) as dag:

    my_task = PythonOperator(
        task_id='my_task',
        python_callable=_my_func,
        provide_context=True
    )
```
The ds return ```AIRFLOW_CTX_EXECUTION_DATE=2022-05-12T20:52:54.642985+00:00```, the context execution data and this is 
how you can make the DAG idempotent.

All operators in Airflow **inherit from BaseOperator class**. This BaseOperator class is available in all operators.
So we should know the BaseOperator class.

## Important Details

### Hoops
Any operator in airflow implement a method called ```execute```. Execute is really the main method taht will be called 
as soon as your task, your operator is triggered.
```python
def execute(self, context:Any):
    """
    This is the main method to drive when creating an operator.
    """
    raise NotImplementedError()
```
There are other methods that can be used but not mandatory as execute like: ```pre_execute``` and this hook is triggered
right after self.execute() is called.
Another method important to know is ```def on_kill(self) -> None``` mostly called when we have sub-processes and we 
should override this method to clean up subprocesses when a task instance gets killed.

There is run method as well wich is really the same to execute, yet it has access to context data unlike execute.


## Task ID
It is unique identifier of your task. Each time creating new operator in a DAG, we should create a task id which should
be unique among all task in a same DAG. Make sure it is meaningful and reflect what the task does as we see it in the 
interface.

- Limitations:
  - Should be string.
  - Max length 250 characters.
  - Alphanumerics, dashes, dots and underscore is only allowed.
  - Cannot be dynamically defined. In airflow we should know the task in advance.
  

## Dag Versioning
how we can deal with changed over time? How about delete a task and create another one with similar task id?
whenever you add a new task and you already trigger your dag, you will see the white squares in the previous DAG runs.
if we delete a task that is run previously? The main problem here is that if you delete a task from a DAG, you do not
have access to the logs of the previously run DAG about that task, and it would be deleted.
- NOTE: To do versioning for the tasks, you can add version on your dag id, for example ```my_dag_v_1_0_0``` and
when you are trying to add new task, you can copy the previous dag python file and change the version.
  
- NOTE: Always add version to your ```dag_id```. 

## Task Owner

In most airflow DAGs you can see the default args file as below:
```
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': airflow.utils.dates.days_ago(3),
    'email': ['it@fff.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}
```
what is the purpose of ``` 'owner': 'airflow'```? In previous version of airflow we have this option to filter the DAG 
based on its owner. If you login with user airflow you were not able to see DAGS by other name owners and vise versa.
In airflow 2.2 new version, this feature is removed. Just the owner can be used to mention that this specific task 
belongs to which user. Each task also can have different owner and we can name them.

Please check the example below:
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from datetime import datetime


default_args = {
    'owner': 'msbeni',
    'start_date': datetime(2022, 5, 11)
}


def _my_func(ds):
    print(ds)


with DAG('my_dag', schedule_interval='@daily', default_args=default_args, catchup=False) as dag:

    my_task = PythonOperator(
        owner='msbeni',
        task_id='my_task_1',
        python_callable=_my_func,
        provide_context=True
    )

    my_task_2 = BashOperator(
        owner='mohasa',
        task_id='my_task_2',
        bash_command="echo 'my task 2'"
    )

    my_task >> my_task_2
```
We have here owner of tasks here. We can see different engineers are working on specific tasks.

## Start Date
This metric defines the date that your task would be started and is really important. There are notes about this metric:
- Two most important parameters already defined in a dag are: **start_date** as the date that the dag will start to run
  and **schedule_interval** as the interval of times that your DAG will be triggered.
  - NOTE: Your DAG would be practically triggered after ```schedule_interval + schedule_interval```, for example if the
  'start_date': datetime(2022, 5, 11) and schedule_interval='@daily', the DAG would be triggered on midnight 
    datetime(2022, 5, 12), but the execution time is shown as set datetime(2022, 5, 11) and for the next day the same.
- catchup=False: if you set the catchup parameter to False, which means you do not want to trigger all the non-triggered
  Dag runs between the last executed dag run and current date, you will have the most recent non-triggered DAG run 
  executed automatically. 
  Remember if you even set the catchup parameter set to false, you will still have the most recent non-triggered DAG 
  run.
  
### Can we set the start_date Dynamically?
If for example set the start_date to datetime.now(), and the schedule_interval to '*/1 * * * *' every minute, nothing
will be run. Because each time the scheduler check the time it will see the ```start_date + schedule_interval``` is 
moving forward and it cannot set a time to start.

You can import ```from airflow.utils.dates import days_ago``` and set the start date like days_ago(5), this can see the 
cron time and set the start date like 5 days ago from cron time.

Use days_ago() can be used to set dynamically, but the best way still is to set it statically like 
```datetime(2022, 5, 12)```.

### Operator's Start Date
Operators can have their own start_date. You can define start_date for each task. The DAG start date will not be 
considered if we have start date for one of our operators. 


## Retry Tasks
There are three important arguments to handle the retries in case of failure in the pipeline:
- 1- **retries** arguments: define the maximum number of retries you can do in case of failure, for example the API is 
  not available. You can set the retries in your task:
  
```python
    my_task_2 = BashOperator(
        owner='mohasa',
        task_id='my_task_2',
        retries=3,
        bash_command="echo 'my task 2'"
    )
```

  the default task retries is set to 0, you can change this by changing the ```default_task_retries``` in the 
  airflow.cfg file and set it to what you want. 

- 2- **retry_delay** argument: This arg expect a time delta object. You can import timedelta from datetime and set it, 
  like example below:
  
```python
    from datetime import datetime, timedelta
    my_task_2 = BashOperator(
        owner='mohasa',
        task_id='my_task_2',
        retries=3,
        retry_delay=timedelta(seconds=10),
        bash_command="echo 'my task 2'"
    )
```
  The task would wait 10 seconds before each retry.

- 3- **retry_exponential_backoff** argument: You might not reach the API for different reasons, maybe many requests are
  sent to the API, by using ```retry_exponential_backoff```, you will increase the time between each retry 
  exponentially. Increasing the reaching time is a smart way to let the API to ba free and probably problem is solved.

```python
    from datetime import datetime, timedelta
    my_task_2 = BashOperator(
        owner='mohasa',
        task_id='my_task_2',
        retries=3,
        retry_exponential_backoff=True,
        retry_delay=timedelta(seconds=10),
        bash_command="echo 'my task 2'"
    )
```

### Now how many times the DAG task is retried
In the batch operator there is a template jinja to do so ```'{{ ti.try_number }}'```.
```python
    from datetime import datetime, timedelta
    my_task_2 = BashOperator(
        owner='mohasa',
        task_id='my_task_2',
        retries=3,
        retry_exponential_backoff=True,
        retry_delay=timedelta(seconds=10),
        bash_command="echo '{{ ti.try_number }}' && echo 'my task 2'"
    )
```

## Be Properly Emailed
How you can be notified if the task fails or is retried? Email Notification is the best way to do that.
- 1- **How to configure airflow to send email?**
  
- 2- **How to receive email in the failure or retries of a task?**
  
  You need a gmail account. (You can do with other providers but the 
  steps are  different). Go to this link in your browser: ```security.google.com/settings/security/apppasswords```, 
  then generate a password that would be used by airflow to sent emails. 
  select app as Mail, for a device select your device, and then click on generate. Save the generated password somewhere
  safe. We will use this password as ```smtp_password``` later.
  In your airflow.cfg file, look for the section ```smtp``` to configure the smtp server to send emails. 
  Apply these changes:
```
[smtp]

# If you want airflow to send emails on retries, failure, and you want to use
# the airflow.utils.email.send_email_smtp function, you have to configure an
# smtp server here
smtp_host = smtp.gmail.com
smtp_starttls = True
smtp_ssl = False
# Example: smtp_user = airflow
smtp_user = your_email@gmail.com
# Example: smtp_password = airflow
smtp_password = password_generated 
smtp_port = 587
smtp_mail_from = your_email@gmail.com
smtp_timeout = 30
smtp_retry_limit = 5
```
  Now restart your airflow and run it again. You should define, email, email_retry and email_fails, the two latter are 
  by default set to True.

  You can add the email in the task to receive the email and also can set the ```email_on_retry``` and 
  ```email_on_failure``` to false. It is based on your preference.
  By using the command ```docker exec -it schedular_image_id /bin/bash``` you can go inside the docker scheduler and run
  airflow command.

  Onw very useful command is ```airflow tasks test dag_id task_id a_previous_date```. For example for a DAG like below:
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from datetime import datetime, timedelta


default_args = {
    'start_date': datetime(2022, 5, 11)
}


def _my_func(ds):
    print(ds)


with DAG('my_dag', schedule_interval='@daily', default_args=default_args, catchup=False) as dag:

    my_task = PythonOperator(
        owner='msbeni',
        task_id='my_task_1',
        python_callable=_my_func,
        provide_context=True
    )

    my_task_2 = BashOperator(
        owner='mohasa',
        task_id='my_task_2',
        email=['your_email@gmail.com'],
        retries=3,
        retry_exponential_backoff=True,
        retry_delay=timedelta(seconds=10),
        bash_command="echo '{{ ti.try_number }}' && exit 1"
    )

    my_task >> my_task_2
```
  you can run this command: ```airflow tasks test my_dag my_task_2 2022-01-01``` and see the email is sent in failure
  to your email or not. ```exit 1``` in ```bash_command``` guarantee the failure of the DAG. You can see the email is
  sent to you. Something like this 
  subject ```Airflow alert: <TaskInstance: my_dag.my_task_2 2022-01-01T00:00:00+00:00 [up_for_retry]>``` and this text:
```
Try 1 out of 4
Exception:
Bash command failed. The command returned a non-zero exit code.
Log: Link
Host: 7b....49b
Log file: /opt/airflow/logs/my_dag/my_task_2/2022-01-01T00:00:00+00:00.log
Mark success: Link
```
  as can be seen we are able to receive the email. You can add the email and ```email_on_retry``` and 
  ```email_on_failure``` in the ```default_args``` to enable the setting for all the tasks of the DAG:
```python
default_args = {
    'owner': 'msbeni',
    'start_date': datetime(2022, 5, 11),
    'email': ['your_email@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': False
}
with DAG('my_dag', schedule_interval='@daily', default_args=default_args, catchup=False) as dag:
    pass
```
  You can also change the ```default_email_on_retry``` and ```default_email_on_failure``` in the airflow.cfg file.
```shell
# Whether email alerts should be sent when a task is retried
default_email_on_retry = True

# Whether email alerts should be sent when a task failed
default_email_on_failure = True
```
  Now we can talk about how to specify the email content.
- 3- **How to customize email alert sent by airflow?** 
  You can open the configuration file of your airflow (airflow.cfg), and add these two changes:
  
```
subject_template = /opt/airflow/includes/subject_template_email.txt
html_content_template = /opt/airflow/includes/content_template_email.txt
```
  - **subject_template**: contains the path lead to the subject of your email.
  - **html_content_template**: File corresponding to the content of your email.
  Once you have done this, then in the includes folder create two files, one ```subject_template_email.txt``` and the
    other one ```content_template_email.txt``` now we have both files ready. 
    We create these files in the includes folder as shown below:
    for **content_template_email.txt** file:
```
Try {{try_number}} out of  {{max_tries + 1}}
Execution date: {{ti.execution_date}}
```
  and for **subject_template_email.txt** file:
```
Airflow alert: {{ti.task_id}}
```
  and if I test this task again on the docker terminal as before, I will receive an email with this subjct
  ```Airflow alert: my_task_2``` and with the below text:
```
Try 1 out of 4 Execution date: 2022-01-01T00:00:00+00:00
```
  very interesting.

## Make Tasks Dependant Between DAG Runs
This is very important to be able to verify if the same task is succeeded in the previous run of the DAG, for example 
the day before, and how to make sure that the previous DAG run was succeeded before running the second DAG run. This 
concept is ```TASK Dependancy between DAG Runs```. When set a parameter depend on past and set it to True and in this 
case the related task will only run if the previous task in the previous DAG run was succeeded. Take these steps to do
this:
  - set catchup=True
  - add **depends_on_past=True** for the task you want to execute.
  This make that task dependent on the previous DAG runs of that task. For the same DAG you can run 16 different DAG
    runs in parallel, all the tasks can be completed but if you have set depends_on_past equal to True and the task 
    failed the tasks related to next DAG runs will not be completed, and we came to a deadlock.
    
  - How to solve this issue? You can add a time out **dagrun_timeout=30** in your DAG definition, teh number is on 
    seconds, and can be anything you want. This is saying that after 30 seconds the DAG run will fail. Always define a 
    time out for your DAG run. 
    
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'msbeni',
    'start_date': datetime(2022, 5, 1),
    'email': ['msbeni@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': True
}

def _my_func(execution_date):
    if execution_date.day == 5:
        raise ValueError("Error")

with DAG('my_dag_v0.0.1', schedule_interval='@daily', default_args=default_args, dagrun_timeout=30, catchup=True) as dag:

    my_task_1 = BashOperator(
        owner='msbeni',
        task_id='my_task_1',
        bash_command="echo 'task 1' && sleep 10"
    )

    my_task_2 = BashOperator(
        owner='mohasa',
        task_id='my_task_2',
        retries=3,
        retry_exponential_backoff=True,
        retry_delay=timedelta(seconds=10),
        bash_command="echo '{{ ti.try_number }}' && exit 0"
    )

    my_task_3 = PythonOperator(
        owner='msbeni',
        task_id='my_task_3',
        python_callable=_my_func,
        depends_on_past=True
    )

    my_task_1 >> my_task_2 >> my_task_3
```
## Wait for Downstream Tasks
With this feature we not only for the previous task to succeed and also for the direct downstream task. When we use the
wait for downstream for a task automatically ```depends_on_past``` will be set to True. It will not only check the same 
task on the previous DAG run, but also check the very next downstream task after that tasks in the previous run was 
successful or not. This will wait and never run the very next downstream of the task and prevent error and problems
```python
    my_task_1 = BashOperator(
        owner='msbeni',
        task_id='my_task_1',
        bash_command="echo 'task 1' && sleep 10",
        wait_for_downstream=True
    )
```
## Pools in Airflow
Pools are used to limit concurrency for a set of tasks. How to limit the tasks to reach a resource, for example a 
database and processing stuff, we can manage how many tasks have access to that resource at the same time, and this can
be applied to the API requests as well. In airflow, you can run up to 32 tasks at the same time, but what if there are 
limitations? In a pool you have a number of worker slots and in running a task some of these slots are called to run 
the task and will be released when the task is done. By default, there is a pool called default_pool and that pool has 
128 worker slots which means you can run at most 128 tasks, and you can change that number.
See the DAG below:
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
from airflow.models.baseoperator import chain
from airflow.utils.task_group import TaskGroup


default_args = {
    'owner': 'msbeni',
    'start_date': datetime(2022, 5, 1),
    'email': ['msbeni@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': True
}


def _my_func(execution_date):
    if execution_date.day == 5:
        raise ValueError("Error")


with DAG('my_dag_v0.0.2', schedule_interval='@daily', default_args=default_args, catchup=False) as dag:

    extract_a = BashOperator(
        owner='msbeni',
        task_id='extract_a',
        bash_command="echo 'task 1' && sleep 10"
    )

    extract_b = BashOperator(
        owner='msbeni',
        task_id='extract_b',
        bash_command="echo 'task 1' && sleep 10"
    )

    with TaskGroup(group_id='group1') as tg1:
        process_a = BashOperator(
            owner='mohasa',
            task_id='process_a',
            retries=3,
            retry_exponential_backoff=True,
            retry_delay=timedelta(seconds=10),
            bash_command="echo '{{ ti.try_number }}' && sleep 20",
            pool="concurrency_limitation_pool"
        )

        process_b = BashOperator(
            owner='mohasa',
            task_id='process_b',
            retries=3,
            retry_exponential_backoff=True,
            retry_delay=timedelta(seconds=10),
            bash_command="echo '{{ ti.try_number }}' && sleep 20",
            pool="concurrency_limitation_pool"
        )

        process_c = BashOperator(
            owner='mohasa',
            task_id='process_c',
            retries=3,
            retry_exponential_backoff=True,
            retry_delay=timedelta(seconds=10),
            bash_command="echo '{{ ti.try_number }}' && sleep 20",
            pool="concurrency_limitation_pool"
        )

        [process_a, process_b, process_c]

    store = PythonOperator(
        owner='msbeni',
        task_id='store',
        python_callable=_my_func,
        depends_on_past=True
    )

    [extract_a, extract_b] >> tg1 >> store
```
Go to the Admin.Pools in the Airflow dashboard, add new pool name it and set number of slots.
Now go back to your code and just put the **pool="name_of_pool"** for the processes you want. As you can see, we setup a
pool and add it in the TaskGroup, **pool="concurrency_limitation_pool"** and all is done perfectly.

- NOTE: You can use **task_concurrency=1** on a task and limit the concurrency without using pool

## Task Priority
If you want to prioritize DAGs or tasks over each other or run a task immediately. There are two parameters that can be
set to do so:
- 1- **priority_weight**: Define the weight of a task. Defined based on the integer and higher the number higher the 
  priority. All tasks by default have the priority 1, but you can manage it. Dependency will be a respected and this 
  priority are respected for the tasks in the same pool.
  
- 2- **priority_rule**: Define how the priority rules of your tasks are computed and there are 3 defined values for the
  which are downstream, upstream and absolute. In the **downstream** priority weight the initial tasks have higher 
  priority and this will change hierarchical, but in the **upstream** is the other way around. Absolute lso does not 
  change anything.

## Change task Execution with Trigger Rules
Define the rules that can change the triggering order.

## Exceptions with SLA
in the airflow.cfg file there is ```check_slas = True```. Then you can use this feature in the pipeline to when the
timedelts is passed it will send you an email notification. 
```python
    store = PythonOperator(
        owner='msbeni',
        task_id='store',
        python_callable=_my_func,
        depends_on_past=True,
        sla= timedelta(15)
    )
```
Or you can even define a function in your DAG to do so:
```python
def _sla_miss(dag, task_list, blocking_task_list, slas, blocking_tis):
  print(f"SLAs for dag: {dag} - SLAs: {slas}")

with DAG('my_dag_v0.0.2', schedule_interval='@daily', 
         default_args=default_args, sla_miss_callback=_sla_miss, catchup=False) as dag:
    pass
```

## Timeout
If a task is sucked and yu want to find out and avoid getting stuck. You can define timeout by the **execution_timeout**
for example 2 minutes nad say if the tasks took more than this time the task will be failed and not run to infinite 
loop. The best timeout value can be found in the dashboard of the airflow when you run the DAG many times and then you 
can check how long a task took to run.  **execution_timeout=timedelta(seconds=12)**
```python
    store = PythonOperator(
        owner='msbeni',
        task_id='store',
        python_callable=_my_func,
        depends_on_past=True,
        execution_timeout=timedelta(seconds=12)
    )
```
- Do we have anything to do in the failure if a task? A callback? There are 4 callbacks that can be used:
  - 1- **on_success_callback**=_on_success_call: call a function and print something
```python
def _on_success_call(context):
  print(context)

def _extract_on_failure(context):
  print(context)

    store = PythonOperator(
        owner='msbeni',
        task_id='store',
        python_callable=_my_func,
        depends_on_past=True,
        on_success_callback=_on_success_call,
        on_failure_callback=_extract_on_failure
    )
```
  
- 2- **on_failure_callback**: The same call a function on failure. there would be a 
  ```'exception': AirflowException(...)``` key defining the error in the returned dictionary.


## XCOMS - Share Data between your Tasks
In airflow each task is independent, but if you want to share data you can use **XCOM** which stands for cross 
communication and is a mechanism to share data between tasks. XCOM is identified by  a key and the key will be used to 
pull the data from other task. A task push the data to the metadata of airflow and the other one pull the data and the 
value in XCOM is serialized in JSON. You have also Timestamp, Execution_date, task_id and dag_id in the metadata. 

### PUSH SCOM
How you can push a XCOM? There are 3 ways to do so:
- 1- **do_xcom_push**: By default is True. 
- 2- **xcom_push**: You can use to push your own XCOMs, for example a value in the python operator. 
- 3- **return**: Whenever you return a value from your operator you are pushing the value to the metadata of the 
  airflow.
  
### PULL XCOM
There is one way, to use **xcom_pull(task_id, key)**

### XCOM Limitation
- 1- XCOM are for a small amount of data not for example for dataframes, in postgresql you are limited to 1 gig, 
  in mysql 64 bytes.

```python
def _my_func(ti, execution_date):
    xcoms = ti.xcom_pull(task_ids=['process_a', 'process_b', 'process_c'], key='return_value')
    if execution_date.day == 5:
        raise ValueError("Error")

    print(xcoms)
```

## Executor Config
You can config your executor, the only executor you can config with executor config is **Kubernetes Executor**. You can 
run different tasks on different pods and you can isolate your tasks from each other. 
You can use this parameter to configure your pod from yur task. 
For example if you have many tasks some computational heavy and some memory heavy jobs or other, you can 
configure the tasks based on the requirement.

```
TASK A  <------- {
                  "KubernetesExecutor:{
                    "request_cpu": "2"
                    "request_memory": "128Mi"
                      }
                    }

TASK B <------- {
                  "KubernetesExecutor:{
                    "request_cpu": "1"
                    "request_memory": "500Mi"
                      }
                    }

TASK C <------- {
                  "KubernetesExecutor:{
                    "request_cpu": "8"
                    "request_memory": "128Mi"
                      }
                    }
```

You can really optimize your resources when working on the teams. In this approach you are limited with what airflow 
ask you to do, and you should wait for airflow to updated to use the new feature of the Kubernetes.

New approach here is to use **pod_override**. With this you have access to entire Kubernetes API, or you can put your 
specification in a file and use **pod_template_file** to add the specification to the task.
```
TASK A  <------- {
                  "pod_override": k8s.V1Pod{
                      spec=k8s.V1PodSpec(...)
                      }
                    }

TASK B <------- {
                  "pod_override": k8s.V1Pod{
                      spec=k8s.V1PodSpec(...)
                      }
                    }

TASK C <------- {
                  "pod_template_file": "/usr/tmp.yaml"
                    }
```
## Providers
Airflow providers are now a package that is absolutely separated from airflow apache core package and we no longer need
to wait for airflow to update its version to be able to use the services of the other providers. So you do not need to 
install all the providers dependencies and deal with them. You just install whatever you need. For example if you want 
work with AWS you will need to install AWS provider.

In order to see the providers you can go to [this](https://registry.astronomer.io/) website and see the documents.
Each time you want to add a python module (to install and use the provider services), add the provider file to the 
**requirements.txt** file to be installed via your custome docker image.

For example let install **great-expectations** library. First copy the installation of the provider along with its 
latest version to the requirements.txt file, in this case: **airflow-provider-great-expectations==0.1.4** 
Then build a new Dockerfile to add this requirements.txt file in it and install the packages. The Dockerfile is almost 
this:
```dockerfile
FROM apache/airflow:2.1.0

COPY requirements.txt .

RUN pip install -r requirements.txt
```

In the docker-compose.yml file instead of **image: apache/airflow:2.1.0** use this:
```dockerfile
build:
    context: .
```

now run ```docker-compose up -d``` to test the installation.



## PythonOperator
Let's learn everything about python operator. In order to pass the argument to the PythoOperator you have two options:
- 1- **op_args**: use op_args=[args]
- 2- **op_kwargs**: you can use a dictionary in this case. See below examples:
```python
from airflow.models import DAG, Variable
from airflow.operators.python import PythonOperator

from datetime import datetime

def _task_1(file_path, file_name):
    print(f"{file_path}/{file_name}")


def _task_2(**kwargs):
    print(f"{kwargs['file_path']}/{kwargs['file_name']}")

def _task_3(**kwargs):
    print(f"{kwargs['file_path']}/{kwargs['file_name']}")

def _task_4(**kwargs):
    print(f"{kwargs['path']}/{kwargs['file_name'] - {kwargs['ds']}}")
    
with DAG('pyDAG', schedule_interval='@daily', start_date=datetime(2022, 5, 13), catchup=False) as dag:

    pyDag_task_1 = PythonOperator(
        task_id='pyDag_task_1',
        owner='mohasa',
        python_callable=_task_1,
        op_args=['/usr/local/airflow', 'data.csv']
    )

    pyDag_task_2 = PythonOperator(
        task_id='pyDag_task_2',
        owner='mohasa',
        python_callable=_task_2,
        op_kwargs={'file_path': '/usr/local/airflow', 'file_name':'data.csv'}
    )

    pyDag_task_3 = PythonOperator(
        task_id='pyDag_task_3',
        owner='mohasa',
        python_callable=_task_3,
        op_kwargs={'file_path': '{{ var.value.path }}', 'file_name':'{{ var.value.file_name }}'}
    )

    pyDag_task_4 = PythonOperator(
        task_id='pyDag_task_4',
        owner='mohasa',
        python_callable=_task_3,
        op_kwargs=Variable.get("vars_json", deserialize_json=True)
```

  If we do want to injest a variable or something at the middle of the pipeline and not a hard coded data?
  You should go to the airflow dashboard and go to the Admin then Variables and create new variable and define your 
  variable. To inject the defined variable at run time you need to use Jinja solution: **{{ var.value.defined_var }}**
  check the example above in ```pyDag_task_3```. 
  
  You can create one JSON variable and add your variables there and call the json variable. It is more efficient.
  See the example above to see an approach like this in ```pyDag_task_4```. I defined a variable like this in airflow 
  Admin Variables section:
  ```	Key: vars_json	Val: {"path":"/usr/bin/airflow", "file_name":"myFileName"}``` and now you can see the DAG.
  

## TaskFlow API
There is a better and faster way to run the python tasks. In TaskFlow API you define your tasks using ```decorators```.
In this approach you do not need to use the python operator anymore and you can use a very simple decorator right on top
of your python function and this would make the python function automatically a python operator. See the example below, 
you should first import ```from airflow.decorators import task``` then check the below:
- NOTE: When you are using the task decorator the name of the function become the task ID. If you want to modify the 
task_id you can do that using the ```@task(task_id="task_id_name")```.
  
- NOTE2: In this form of calling python decorator you do not have access to the Context anymore and to call the Context
  you need to import ```get_current_context``` from ```airflow.operators.python```.
  
- NOTE3: You can mix this task operator with other operators. Check the code below:

```python
from airflow.models import DAG, Variable
from airflow.decorators import task
from airflow.operators.python import get_current_context
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta


@task(task_id="dec_task_1")
def process(func_vars):
    context = get_current_context()
    print(f"{func_vars['path']}/{func_vars['file_name']} - {context['ds']}")


with DAG('pyDAGdec', schedule_interval='@daily', start_date=datetime(2022, 5, 13), catchup=False) as dag:

    store = BashOperator(
        task_id="store",
        bash_command="echo 'store is called'"
    )

    process(Variable.get("vars_json", deserialize_json=True)) >> store
```

## BashOperator
There are many undiscovered features related to BashOperator. 
Always remember that you can call the bash commands from a ```.sh``` file in the DAG folder, like below:
```python
from airflow.models import DAG, Variable
from airflow.operators.bash import BashOperator

from datetime import datetime


with DAG('myBashDAG', schedule_interval='@daily', start_date=datetime(2022, 5, 14), catchup=False) as dag:

    bash_task_1 = BashOperator(
        task_id='bash_task_1',
        owner='msbeni',
        bash_command="scripts/commands.sh"
    )
```
and the file ```commands.sh``` in the scripts' folder can be like this:
```shell
#!/bin/bash

echo 'execute my command'
exit 0
```
```#!/bin/bash``` is used to instruct the operating system to use bash as a command interpreter. This running from a 
file is a cleaner and optimized approach. In XCOM you can see the ```return_value``` as ```execute my command``` and 
by adding the ```do_xcom_push=False``` to the task definition in the DAG you can deactivate this feature, like below:
```python
    bash_task_1 = BashOperator(
        task_id='bash_task_1',
        owner='msbeni',
        bash_command="scripts/commands.sh",
        do_xcom_push=False
    )
```
- NOTE: One security issue related to the BashOperator is that it is able to have access to all the environment 
  variables from the machine where it is executed just by putting ```env``` as a bash command. You can prevent this
  security issue by defining the env vars as the key and values.
  
```python
    bash_task_1 = BashOperator(
        task_id='bash_task_1',
        owner='msbeni',
        bash_command="scripts/commands.sh",
        do_xcom_push=False,
        env={
          "MY_VAR":"MY_VALUE"
        }
    )
```

- NOTE: You can define an environment variable my the above mentioned feature from the airflow environment variables by
  using the env feature and define it as below:
  
```python
    bash_task_1 = BashOperator(
        task_id='bash_task_1',
        owner='msbeni',
        bash_command="scripts/commands.sh",
        do_xcom_push=False,
        env={
          "api_aws":"{{ var.value.api_key_aws }}"
        }
    )
```
  This means this value will be added at run time. All the env vars which seems to be a key or secret will be return 
  and shown with ```***``` to keep them secure like this output: ```api_aws=***```. You can run this in your bash script
  as well:
  
```bash
#!/bin/bash

echo 'api_aws: {{ var.value.api_key_aws}}'
exit 0
```
- NOTE: You can skip a task by using: ```exit 99``` in the bash command, or you can define your own exit code in the 
  task definition using: ```skip_exit_code=10```.
  
```python
    bash_task_1 = BashOperator(
        task_id='bash_task_1',
        owner='msbeni',
        bash_command="scripts/commands.sh",
        skip_exit_code=10,
        do_xcom_push=False,
        env={
          "api_aws":"{{ var.value.api_key_aws }}"
        }
    )
```
 and then the ```.sh``` file as this:
 
```shell
#!/bin/bash
whoami
echo 'api_aws: {{ var.value.api_key_aws}}'
exit 10
```
  The ```whoami``` is used to see who is executing the bash command.
  

## PostgresOperator
What if you want to interact with your airflow DB and add data dynamically anf other operations? First you should import 
**PostgresOperator** like this ```from airflow.providers.postgres.operators.postgres import PostgresOperator``` and as 
it is called from a provider you should first install the postgres provider.
check the list of your providers use this command:
```shell
docker exec scheduler_docker_id airflow providers list
```
Create a DAG like below to run a sql command:
```python
from airflow.models import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime

with DAG('myPostgresDAG', schedule_interval='@daily', start_date=datetime(2022, 5, 14), catchup=False) as dag:
    create_table = PostgresOperator(
        task_id='create_table',
        postgres_conn_id='postgres',
        sql="CREATE TABLE my_table (table_val TEXT NOT NULL, PRIMARY KEY (table_val))"
    )  
  
  
    store = PostgresOperator(
          task_id='store',
          postgres_conn_id='postgres',
          sql="INSERT INTO my_table VALUES ('my_value')"
      )
```
and go to the Airflow Dashboard in Admin the Connections, and add a new record:
```
Conn Id *	 postgres
Conn Type postgres	
Host	postgres
Schema	
Login	postgres
Password	postgres
Port	5432
```
 and then in the bash session of the scheduler docker to interact with airflow CLI, test the tasks, specifically the 
 table creation task:
 
```bash
airflow tasks test myPostgresDAG create_table 2022-01-01
```
now you can check inside your postgres db in docker bash to check the table, sign in to the postgres by this command:
```shell
root@d5aae118f76e:/# psql -Upostgres
```
This is the result:
```postgresql
postgres=# \dt;
          List of relations
 Schema |   Name   | Type  |  Owner   
--------+----------+-------+----------
 public | my_table | table | postgres
(1 row)
```
and then test the other task, store and the result:
```postgresql
postgres=# select * from my_table;
 table_val 
-----------
 my_value
(1 row)
```
- NOTE; Best practices to work with the postgres is not to put query itself in the task body, you should create a file 
  and call the file containing the query:
  CREATE a directory and out all .sql files there for example, ```CREATE_TABLE_MT_TABLE.sql``` file, and copy your sql 
  in it:
  
```postgresql
CREATE TABLE IF NOT EXISTS my_table (table_val TEXT NOT NULL, PRIMARY KEY (table_val));
```
  and then the task would be like this:
  
```python
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime

with DAG('myPostgresDAG', schedule_interval='@daily', start_date=datetime(2022, 5, 14), catchup=False) as dag:
    create_table = PostgresOperator(
        task_id='create_table',
        postgres_conn_id='postgres',
        sql="sql/CREATE_TABLE_MT_TABLE.sql"
    )  
```
- NOTE: put ```IF NOT EXISTS``` to make sure the DAG and task is idempotent.
- NOTE2: You can run multiple sql requests as well. Just out them in a list like below:
```python
from airflow.models import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator

from datetime import datetime


with DAG('myPostgresDAG', schedule_interval='@daily', start_date=datetime(2022, 5, 14), catchup=False) as dag:
    create_table = PostgresOperator(
        task_id='create_table',
        postgres_conn_id='postgres',
        sql="sql/CREATE_TABLE_MT_TABLE.sql"
    )

    store = PostgresOperator(
        task_id='store',
        postgres_conn_id='postgres',
        sql=[
            "sql/INSERT_INTO_MY_TABLE.sql",
            "SELECT * FROM my_table;"
            ]
    )
```
 Be careful with the PostgresOperator you are **not able to fetch rows** from a table. This can be only done by writing 
 your own operator over it and use postgres hook.
 

## Pass Dynamic Parameters to PostgresOperator
This is a very famous question. To add the parameters to your sql request you need to use another argument in your 
PostgresOperator called ```parameters```.  With parameters, you can define a dictionary of parameters you want to pass. 
See below:
```python
from airflow.models import DAG, Variable
from airflow.providers.postgres.operators.postgres import PostgresOperator

from datetime import datetime


with DAG('myPostgresDAG', schedule_interval='@daily', start_date=datetime(2022, 5, 14), catchup=False) as dag:
    create_table = PostgresOperator(
        task_id='create_table',
        postgres_conn_id='postgres',
        sql="sql/CREATE_TABLE_MT_TABLE.sql"
    )

    store = PostgresOperator(
        task_id='store',
        postgres_conn_id='postgres',
        sql=[
            "sql/INSERT_INTO_MY_TABLE.sql",
            "SELECT * FROM my_table;"
            ],
        parameters={
          'filename': 'data.csv'
        }
        
    )
```
  How we can pass this parameters to our sql request???? Go to your sql request and add these changes:
  

```postgresql
INSERT INTO my_table 
    VALUES (%(filename)s)
ON CONFLICT(table_val)
DO UPDATE 
    SET table_val='my_new_val';
```
  for the ```VALUES  ('my_value')``` we replace the **VALUES (%(filename)s)**. 
  
Now the question is how to do this dynamically. With the argument parameters this is impossible to add data 
dynamically. You can add a new Operator on top of your PostgresOperator to do this, to add the parameters as an
argument to be added in the run time. Let's do this:
```python
class CustomPostgresOperator(PostgresOperator):
    template_fields = ('sql', 'parameters')
```
Just by adding this class inheriting from ```PostgresOperator```. The DAG would be as follows:
```python
from airflow.models import DAG, Variable
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python import PythonOperator

from datetime import datetime


class CustomPostgresOperator(PostgresOperator):
    template_fields = ('sql', 'parameters')


def _my_task():
    return 'tweets.csv'


with DAG('myPostgresDAG', schedule_interval='@daily', start_date=datetime(2022, 5, 14), catchup=False) as dag:
    create_table = PostgresOperator(
        task_id='create_table',
        postgres_conn_id='postgres',
        sql="sql/CREATE_TABLE_MT_TABLE.sql"
    )

    my_psql_task = PythonOperator(
        task_id='my_psql_task',
        python_callable=_my_task
    )

    store = CustomPostgresOperator(
        task_id='store',
        postgres_conn_id='postgres',
        sql=[
            "sql/INSERT_INTO_MY_TABLE.sql",
            "SELECT * FROM my_table;"
            ],
        parameters={
          'filename': '{{ ti.xcom_pull(task_ids=["my_psql_task"]}}'
        }
    )
```
  In this DAG we are fetching the XCOMs that are pushed by previous task and put it as the value of the parameter
  ```filename``` dynamically. Test the new tasks and the result would be amazing:
  
```postgresql
postgres=# select * from my_table;
   table_val    
----------------
 my_new_val
 data.csv
 ['tweets.csv']
```

## BranchPythonOperator
This operator enables you to run a specific task based on a condition. For example if the ML model is accurate publish 
it and of not retrain the model. The solution is easy: You should provide a python_callable usually a python function 
and define condition in it. In this case the next task for example ```publish_ml``` will be skipped as one of the tasks 
are not executed. How we can solve the issue like this. For this purpose you need to use ```trigger_rule```. This rule
modifies the way that your task will be executed. By default, ot is all_success, see the following DAG:
```python
from airflow.models import DAG, Variable
from airflow.operators.python import BranchPythonOperator
from airflow.operators.dummy import DummyOperator

from datetime import datetime

def _check_accuracy():
    accuracy = 0.16
    if accuracy > 0.15:
        return ['accurate', 'top_accurate']
    return 'inaccurate'

with DAG('myBranchpyDAG', schedule_interval='@daily', start_date=datetime(2022, 5, 14), catchup=False) as dag:
    training_ml = DummyOperator(task_id='training_ml')
    check_accuracy = BranchPythonOperator(
        task_id='check_accuracy',
        python_callable=_check_accuracy
    )
    accurate = DummyOperator(task_id='accurate')
    top_accurate = DummyOperator(task_id='top_accurate')
    
    inaccurate = DummyOperator(task_id='inaccurate')

    publish_ml = DummyOperator(task_id='publish_ml', trigger_rule='none_failed_or_skipped')

    training_ml >> check_accuracy >> [accurate, inaccurate] >> publish_ml
```
You can return multiple tasks to be run in the BranchPythonOperator.

## Schedule DAGs Based on Calendar
With default schedule_interval you are not add calendar. You can do this by using the ```BranchPythonOperator``` and a
python script checking the data if it is reached. We want to stop our DAG in the days-off, and we create a days_off.yml
file in the files folder. First ```import yaml```, open the file in the python function and set the conditions as 
follows:
```python
from airflow.models import DAG, Variable
from airflow.operators.python import BranchPythonOperator
from airflow.operators.dummy import DummyOperator

from datetime import datetime
import yaml


def _check_holidays(ds):   # ds is the DAG Execution Date
    with open('dags/files/days_off.yml', 'r') as f:
        days_off = set(yaml.load(f, loader=yaml.FullLoader))
        if ds not in days_off:
            return 'process_data'
    return 'stop_processing'


with DAG('myBranchCalendarDAG', schedule_interval='@daily', start_date=datetime(2022, 5, 14), catchup=False) as dag:

    check_holidays = BranchPythonOperator(
        task_id='check_holidays',
        python_callable=_check_holidays
    )
    process_data = DummyOperator(task_id='process_data')
    cleaning_data = DummyOperator(task_id='claening_data')
    stop_processing = DummyOperator(task_id='stop_processing')

    check_holidays >> [process_data, stop_processing]
    process_data  >> cleaning_data
```

## BranchSQLOperator
If you want to choose a task based on a value in the DB, this is where this operator become important. In the DAG below 
this feature is practiced:
```python
from airflow.models import DAG, Variable
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.sql import BranchSQLOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime
import yaml

with DAG('myBranchSQLDAG', schedule_interval='@daily', start_date=datetime(2022, 5, 14), catchup=False) as dag:

    branch_craete_table = PostgresOperator(
        task_id='branch_craete_table',
        sql='sql/CREATE_TABLE_PARTNERS.sql',
        postgres_conn_id='postgres',
    )
    branch_insert_into_table = PostgresOperator(
        task_id='branch_insert_into_table',
        sql='sql/INSERT_INTO_PRTNERS.sql',
        postgres_conn_id='postgres',
    )
    choose_next_task = BranchSQLOperator(
        task_id='choose_next_task',
        sql="SELECT COUNT(1) FROM partners WHERE partner_status=TRUE",
        follow_task_ids_if_true=['process_sql'],
        follow_task_ids_if_false=['notif_email', 'notif_slack'],
        conn_id='postgres',
    )
    process_sql = DummyOperator(task_id='process_sql')
    notif_email = DummyOperator(task_id='notif_email')
    notif_slack = DummyOperator(task_id='notif_slack')

    branch_craete_table >> branch_insert_into_table >> choose_next_task >> [process_sql, notif_email, notif_slack]
```
As can be seen in this DAg the ```BranchSQLOperator``` is used to check a condition in a table and based on the result, 
it will make decision to go with whicj next tasks. ```follow_task_ids_if_true``` for the true condition and 
```follow_task_ids_if_false``` for the false one show the next operators.


## BranchDateTimeOperator
If you want to say that if a DAG is triggered between a specific time execute it and otherwise do nothing, we can use 
this approach. This is really the same the other Branch Operators and in the case of the task triggering time is between
**target_lower** and **target_upper** the tasks defined in a list in **follow_task_ids_if_true** will be triggered, 
otherwise tasks in **follow_task_ids_if_false** will be triggered. See the DAG below. Please note that the parameter 
```use_task_execution_date``` will check whether the current execution time of the DAG (not current date) is between the 
time mentioned or not and we do not need to check the date and time is enough.
```python
from airflow.models import DAG
from airflow.operators.datetime import BranchDateTimeOperator
from airflow.operators.dummy import DummyOperator

from datetime import datetime, time

with DAG('myBranchSQLDAG', schedule_interval='@daily', start_date=datetime(2022, 5, 14), catchup=False) as dag:
    is_in_time_frame = BranchDateTimeOperator(
        task_id='is_in_time_frame',
        follow_task_ids_if_true=['move_forward'],
        follow_task_ids_if_false=['end_dag'],
        target_lower=time(10, 0, 0),
        target_upper=time(11, 0, 0),
        use_task_execution_date=True
    )

    move_forward = DummyOperator(task_id='move_forward')
    end_dag = DummyOperator(task_id='end_dag')

    is_in_time_frame >> [move_forward, end_dag]
```

## BranchDayOfWeekOperator
This operator is used to create different trigger interval for different tasks in a DAG. See the DAG below and check the
solution. Easy and pretty the same of the other Branch Operators. 

```python
from airflow.models import DAG
from airflow.operators.dummy import DummyOperator
from airflow.operators.weekday import BranchDayOfWeekOperator
from airflow.utils.weekday import WeekDay

from datetime import datetime, time

with DAG('myBranchWeekDayDAG', schedule_interval='@daily', start_date=datetime(2022, 5, 14), catchup=False) as dag:

    task_a_bdwo = DummyOperator(task_id='task_a_bdwo')
    task_b_bdwo = DummyOperator(task_id='task_b_bdwo')

    is_wednesday = BranchDayOfWeekOperator(
        task_id='is_wednesday',
        follow_task_ids_if_true=['task_c_bdwo'],
        follow_task_ids_if_false=['task_end'],
        week_day=WeekDay.WEDNESDAY,
        use_task_execution_day=False,
    )
    task_c_bdwo = DummyOperator(task_id='task_c_bdwo')
    task_end = DummyOperator(task_id='task_end')

    task_a_bdwo >> task_b_bdwo >> is_wednesday >> [task_c_bdwo, task_end]
```

## SubDagOperator
How to create DAG dependencies in Airflow? There are different dags and you want new visualization and showing the 
parent dag and child dags.
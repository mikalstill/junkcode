This demo runs a simple terraform HTTP state server written in python.
The protocol that these servers talk isn't well documented (that I could
find), so I wanted to explore that.

To use this state server, configure your terraform file as per demo.tf.
The important bits are:

~~~
terraform {
  backend "http" {
    address = "http://localhost:5001/terraform_state/4cdd0c76-d78b-11e9-9bea-db9cd8374f3a"
    lock_address = "http://localhost:5001/terraform_lock/4cdd0c76-d78b-11e9-9bea-db9cd8374f3a"
    lock_method = "PUT"
    unlock_address = "http://localhost:5001/terraform_lock/4cdd0c76-d78b-11e9-9bea-db9cd8374f3a"
    unlock_method = "DELETE"
  }
}
~~~

Where the URL to the state server will obviously change. The UUID in the URL is an example
of an external ID you might use to correlate the terraform state with the system that
requested it be built.

I am using PUT and DELETE for locks due to limitations in the HTTP verbs that the python
flask framework exposes. You might be able to get away with the defaults in other languages or
frameworks.

To run the python server, make a venv, install the dependancies, and then run:

~~~
$ python3 -m venv ~/virtualenvs/remote_state
$ . ~/virtualenvs/remote_state/bin/activate
$ pip install -U -r requirements.txt
$ python stateserver.py
~~~

This demo creates a simple apache web server with the contents of the web site
coming from an attached EBS volume. There is some fancy to ensure the EBS
volume has a filesystem (via a script run by cloud-init and passed via
user-data), and that the volume is mounted on boot.

This demo relies on the AWS provider, which needs credentials setup. If you
haven't done that already, I'd recommend doing it in a python virtualenv. Set
that up like this:

~~~
$ python3 -m venv ~/virtualenvs/aws
$ . ~/virtualenvs/aws/bin/activate
$ pip install -U awscli
~~~

And then setup AWS credentials:

~~~
$ aws configure
AWS Access Key ID [None]: ...snip...
AWS Secret Access Key [None]: ...snip...
Default region name [None]: ...snip...
Default output format [None]: 
~~~

Now we can use terraform like this:

~~~
$ terraform init
$ terraform plan
~~~

And then if the plan doesn't look bonkers:

~~~
$ terraform apply
~~~
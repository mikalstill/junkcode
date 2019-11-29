How do you upgrade to a remote state server? Well, first off read and setup
the remote_state server described in the parent directory. Then come back here
and we'll run some experiments.

demo.tf in this directory starts with a local state backend (the default). You
can see this because the backend configuration is commented out. Create the AWS
resources:

~~~
$ terraform init
$ terraform plan
$ terraform apply
~~~

You should now have an EC2 instance running, and state in a file named
terraform.tfstate in the local directory. Now uncomment the backend configuration
in demo.tf and make sure you're running the python state server demo. Now when
you re-init, the state will be copied to the remote backend:

~~~
$ terraform init

Initializing the backend...
Do you want to copy existing state to the new backend?
  Pre-existing state was found while migrating the previous "local" backend to the
  newly configured "http" backend. No existing state was found in the newly
  configured "http" backend. Do you want to copy this state to the new "http"
  backend? Enter "yes" to copy and "no" to start with an empty state.

  Enter a value: yes


Successfully configured the backend "http"! Terraform will automatically
use this backend unless the backend configuration changes.
~~~

Interestingly, the terraform.tfstate file remains on local disk.